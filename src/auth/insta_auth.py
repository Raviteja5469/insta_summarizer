import time
import re
import webbrowser
import instaloader
from pathlib import Path
from instaloader.exceptions import LoginException
from src.config import logger, Config

def get_authenticated_loader(loader: instaloader.Instaloader, max_login_attempts: int = 2):
    """
    Ensures the Instaloader instance is authenticated.

    This function handles loading a saved session, performing a fresh login,
    and guiding the user through interactive login challenges (checkpoints).
    It modifies the loader instance in-place.
    """
    username = Config.INSTA_USERNAME
    password = Config.INSTA_PASSWORD

    if not username or not password:
        logger.debug("No Instagram credentials configured; proceeding unauthenticated.")
        return

    # Standardize session file path
    safe_username = "".join(c for c in username if c.isalnum() or c in ("-", "_")).rstrip(".-_")
    session_path = Path(Config.TEMP_DIR) / f"session-{safe_username}"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Try loading the session file first
    try:
        logger.debug(f"Attempting to load session from: {session_path}")
        loader.load_session_from_file(username, str(session_path))
        logger.info(f"🔐 Loaded saved Instagram session for '{username}'.")
        return
    except FileNotFoundError:
        logger.info("No saved session found, will attempt a new login.")
    except Exception as e:
        logger.warning(f"Failed to load session file ({e}), attempting a new login.")

    # 2. If session fails, attempt to login
    for attempt in range(1, max_login_attempts + 1):
        try:
            logger.info(f"Attempting Instagram login for '{username}' (attempt {attempt}/{max_login_attempts})...")
            loader.login(username, password)
            
            # Save session on successful login
            loader.save_session_to_file(str(session_path))
            logger.info(f"✅ Logged in to Instagram and saved session to {session_path.name}.")
            return

        except LoginException as e:
            msg = str(e)
            match = re.search(r"https?://[^\s]+", msg)
            if "checkpoint_required" in msg and match:
                challenge_url = match.group(0)
                logger.warning("❗️ Login requires a checkpoint/challenge.")
                logger.warning(f"Please open this URL in your browser to verify: {challenge_url}")
                
                try:
                    webbrowser.open(challenge_url)
                except Exception:
                    logger.debug("webbrowser.open failed; please open the URL manually.")

                input("--> After completing the verification in your browser, press Enter here to continue...")
                
                # After user completes challenge, retry login immediately
                try:
                    logger.info("Retrying login after challenge...")
                    loader.login(username, password)
                    loader.save_session_to_file(str(session_path))
                    logger.info("✅ Successfully logged in after challenge.")
                    return
                except Exception as e2:
                    logger.error(f"❌ Still failed to login after challenge: {e2}")
                    break # Exit loop after failed challenge
            else:
                logger.error(f"❌ Instagram login failed: {msg}")

        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during login attempt {attempt}: {e}")

        if attempt < max_login_attempts:
            wait = 2 ** attempt
            logger.info(f"Waiting for {wait}s before retrying...")
            time.sleep(wait)

    logger.warning("Could not establish an authenticated session. Proceeding unauthenticated (requests may be rate-limited).")
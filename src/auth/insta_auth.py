import time
import re
import webbrowser
import instaloader
from pathlib import Path
from instaloader.exceptions import LoginException
from src.config import logger, Config

def get_authenticated_loader(loader: instaloader.Instaloader, max_login_attempts: int = 2):
    """
    Ensures the Instaloader instance is authenticated by loading a session or
    performing a fresh login with checkpoint handling.
    """
    username = Config.INSTA_USERNAME
    password = Config.INSTA_PASSWORD

    if not username or not password:
        logger.warning("Instagram credentials are not configured. Proceeding unauthenticated.")
        return

    # Standardize session file path for safety
    safe_username = "".join(c for c in username if c.isalnum() or c in ("-", "_")).rstrip(".-_")
    session_path = Path(Config.TEMP_DIR) / f"session-{safe_username}"
    session_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Try loading the session file first (this is the best-case scenario)
    try:
        logger.debug(f"Attempting to load session for '{username}' from: {session_path}")
        loader.load_session_from_file(username, str(session_path))
        logger.info(f"✅ Successfully loaded saved Instagram session for '{username}'.")
        return
    except FileNotFoundError:
        logger.warning("No saved session file found. A new login will be required.")
    except (IOError, EOFError) as e:
        logger.warning(f"Session file is corrupted or unreadable ({e}). Will attempt a new login.")
    except Exception as e:
        logger.warning(f"An unexpected error occurred loading the session file ({e}). Attempting a new login.")

    # 2. If session fails, attempt a fresh login
    logger.info("Proceeding with a fresh login attempt.")
    for attempt in range(1, max_login_attempts + 1):
        try:
            logger.info(f"Attempting Instagram login for '{username}' (Attempt {attempt}/{max_login_attempts})...")
            loader.login(username, password)
            
            # Save session on successful login to avoid this process next time
            logger.info("Login successful. Saving session to file...")
            loader.save_session_to_file(str(session_path))
            logger.info(f"✅ Session for '{username}' saved to {session_path.name}.")
            return

        except LoginException as e:
            msg = str(e)
            match = re.search(r"https?://[^\s]+", msg)

            if "checkpoint_required" in msg and match:
                challenge_url = match.group(0)
                logger.critical("❗️ ACTION REQUIRED: Instagram login requires a checkpoint/challenge.")
                logger.warning(f"Please open this URL in your browser to verify your identity: {challenge_url}")
                
                try:
                    webbrowser.open(challenge_url)
                except Exception:
                    logger.warning("Could not automatically open web browser. Please open the URL manually.")

                input("--> After completing the verification in your browser, press Enter here to continue...")
                
                # Retry login immediately after user confirms challenge completion
                try:
                    logger.info("Retrying login after manual challenge completion...")
                    loader.login(username, password)
                    loader.save_session_to_file(str(session_path))
                    logger.info("✅ Successfully logged in and saved session after challenge.")
                    return
                except Exception as e2:
                    logger.error(f"❌ Still failed to login after completing the challenge: {e2}")
                    break # Exit the loop, something is wrong
            else:
                logger.error(f"❌ Instagram login failed with an unrecoverable error: {msg}")
                break # Exit loop on other login errors
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during login attempt {attempt}: {e}")

        if attempt < max_login_attempts:
            wait = 5 * attempt
            logger.info(f"Waiting for {wait}s before retrying...")
            time.sleep(wait)

    logger.critical("Could not establish an authenticated session. The script will proceed unauthenticated and will likely fail.")
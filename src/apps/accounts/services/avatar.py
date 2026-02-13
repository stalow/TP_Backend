import hashlib


def get_avatar_url(user_id: int, email: str) -> str:
    """
    Generate a deterministic placeholder avatar URL.
    Uses DiceBear Avatars API with a hash of the user's email.
    """
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    # Using DiceBear's thumbs style for friendly placeholder avatars
    return f"https://api.dicebear.com/7.x/thumbs/svg?seed={email_hash}"

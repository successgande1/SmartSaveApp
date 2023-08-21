from .models import Profile
def get_profile(user):
    try:
        return Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return None

def profile_complete(profile):
    if profile is None:
        return False
    return (
        profile.full_name and
        profile.phone and
        profile.address and
        profile.image != 'avatar.jpg'
    )

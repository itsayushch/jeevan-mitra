from typing import Dict, Any, List

def education_to_rank(edu_str: str) -> int:
    s = edu_str.lower()
    if 'degree' in s or 'graduate' in s or 'ba' in s or 'bsc' in s:
        return 5
    if '12' in s or 'inter' in s or 'higher' in s:
        return 4
    if '10' in s or 'matric' in s:
        return 3
    if '8' in s or 'middle' in s:
        return 2
    if '5' in s or 'primary' in s:
        return 1
    return 0

def validate_profile_answers(profile: Dict[str, Any]) -> List[str]:
    errors = []
    if not profile.get("district"):
        errors.append("District is required.")
    if not profile.get("block"):
        errors.append("Block is required.")
    return errors

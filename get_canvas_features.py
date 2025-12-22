import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_canvas_features():
    canvas_url = os.getenv("CANVAS_URL", "").replace("/api/v1", "")
    canvas_token = os.getenv("CANVAS_TOKEN", "")
    
    
    # url = f"{canvas_url}/api/v1/users/self"
    url = f"{canvas_url}/api/v1/accounts/1/features"
    headers = {"Authorization": f"Bearer {canvas_token}"}
    response = requests.get(url, headers=headers)

    # url = f"{canvas_url}/api/v1/features"
    # response = requests.get(url, headers=headers)
    return response.json() if response.ok else {"error": response.status_code}

if __name__ == "__main__":
    features = get_canvas_features()
    print(features)


[
    {
        'feature': 'anonymous_instructor_annotations',
        'applies_to': 'Course',
        'root_opt_in': False,
        'type': 'setting',
        'display_name': 'Anonymous Instructor Annotations',
        'description': 'Anonymize all instructor comments and annotations within DocViewer',
        'feature_flag': {
            'feature': 'anonymous_instructor_annotations',
            'context_id': 1,
            'context_type': 'Account',
            'state': 'allowed_on',
            'locking_account_id': None,
            'transitions': {
                'off': {'locked': False},
                'on': {'locked': False},
                'allowed': {'locked': False},
            },
            'locked': False,
            'parent_state': 'allowed',
        }
    },
    {
        'feature': 'embedded_release_notes',
        'applies_to':'Account',
        'type': 'setting',
        'display_name': 'Embedded Release Notes',
        'description': 'Show Instructure-provided release notes in the Help Menu.',
        'feature_flag': {
            'feature': 'embedded_release_notes',
            'state': 'allowed_on',
            'transitions': {
                'off': {'locked': False},
                'on': {'locked': False},
                'allowed': {'locked': False},
            },
            'locked': False,
            'parent_state': 'allowed_on',
        },
    },
    {
        'feature': 'encrypted_sourcedids',
        'applies_to': 'RootAccount',
        'root_opt_in': True,
        'type': 'setting',
        'display_name': 'Encrypted Sourcedids for Basic Outcomes',
        'description': 'If enabled, Sourcedids used by Canvas for Basic Outcomes will be encrypted.',
        'feature_flag': {
            'feature': 'encrypted_sourcedids',
            'context_id': 1,
            'context_type': 'Account',
            'state': 'off',
            'locking_account_id': None,
            'transitions': {
                'on': {'locked': False},
                'allowed': {'locked': True},
                'allowed_on': {'locked': True},
            },
            'locked': False,
            'parent_state': 'off',
        },
    },
    {
        'feature': 'epub_export',
        'applies_to': 'Course',
        'root_opt_in': True,
        'type': 'setting',
        'display_name': 'ePub Exporting',
        'description': 'This enables users to generate and download course ePub.',
        'feature_flag': {
            'feature': 'epub_export',
            'context_id': 1,
            'context_type': 'Account',
            'state': 'on',
            'locking_account_id': None,
            'transitions': {
                'off': {'locked': False},
                'allowed': {'locked': False},
                'allowed_on': {'locked': False},
            },
            'locked': False,
            'parent_state': 'off',
        },
    },
    {
        'feature': 'filter_speed_grader_by_student_group',
        'applies_to': 'RootAccount',
        'root_opt_in': True,
        'type': 'feature_option',
        'display_name': 'Filter SpeedGrader by Student Group',
        'description': 'Allows users to enable the "Launch SpeedGrader Filtered by Student Group" option for courses on the course settings page. When active and a student group has been selected in New Gradebook, SpeedGrader will only load students in the selected group.',
        'feature_flag': {
            'feature': 'filter_speed_grader_by_student_group',
            'context_id': 170000000000002,
            'context_type': 'Account',
            'state': 'on',
            'locking_account_id': None,
            'transitions': {
                'off': {'locked': False},
                'allowed': {'locked': True},
                'allowed_on': {'locked': True},
            },
            'locked': True,
            'parent_state': 'on',
        },
    },
    {
        'feature': 'final_grades_override',
        'applies_to': 'Course',
        'root_opt_in': True,
        'type': 'setting',
        'display_name': 'Final Grade Override',
        'description': 'Enable ability to alter the final grade for the entire course without changing scores for assignments.',
        'feature_flag': {
            'feature': 'final_grades_override',
            'context_id': 1,
            'context_type': 'Account',
            'state': 'on',
            'locking_account_id': None,
            'transitions': {
                'off': {'locked': True},
                'allowed': {'locked': True},
                'allowed_on': {'locked': False},
                'on': {},
            },
            'locked': False,
            'parent_state': 'off',
        },
    },
]

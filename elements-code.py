import json
import ret

def extract_specific_metadata(file_path):
#    with open(file_path, 'r') as file:
#        data = json.load(file)
        
    data = json.loads(file_path)
    
    metadata = data['metadata']
    
    result = {
        'name': metadata.get('name', 'N/A'),
        'Path': 'N/A',
        'Tape': 'N/A',
        'Camroll': 'N/A',
        'Comments': 'N/A',
        'COUNTRY': 'N/A',
        'Description': 'N/A'
    }

    # Direct access to system fields
    system_dict = {item['name']: item['value'] for item in metadata.get('system', [])}
    result['Path'] = system_dict.get('Path', 'N/A')
    result['Tape'] = system_dict.get('Tape', 'N/A')

    # Direct access to user fields
    user_dict = {item['name']: item['value'] for item in metadata.get('user', [])}
    result['Camroll'] = user_dict.get('Camroll', 'N/A')
    result['Comments'] = user_dict.get('Comments', 'N/A')
    result['COUNTRY'] = user_dict.get('COUNTRY', 'N/A')
    result['Description'] = user_dict.get('Description', 'N/A')

    return result


input_string = """{"metadata": {"name": "test", "system": [{"name": "Path", "value": "/test/path"}, {"name": "Tape", "value": "TestTape"}], "user": [{"name": "Camroll", "value": "TestCamroll"}, {"name": "Comments", "value": "Test comment"}, {"name": "COUNTRY", "value": "TestCountry"}, {"name": "Description", "value": "Test description"}]}}"""

#result = extract_specific_metadata('elements-input.txt')
result = extract_specific_metadata(input_string)
for key, value in result.items():
    ret(key, value)
    print(f"Processed: {key} = {value}")


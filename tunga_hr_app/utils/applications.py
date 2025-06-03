from datetime import datetime


def generate_organization_code(company_name):

    words_in_company_name = company_name.split()
    
    # If the name has multiple words_in_company_name, use the first letter of each word
    if len(words_in_company_name) > 1:
        code = ''.join(word[0] for word in words_in_company_name).upper()
    else:
        code = company_name[:3].upper()
    
    return code
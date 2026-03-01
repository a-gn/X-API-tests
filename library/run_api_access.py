from a_gn_x_api_tests.check_access import check_access
from a_gn_x_api_tests.credentials import load_credentials

if __name__ == "__main__":
    check_access(load_credentials())
    print("Success!")

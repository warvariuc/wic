#!/usr/bin/python3

if __name__ == "__main__":
    import unittest
    all_tests = unittest.TestLoader().discover('tests', pattern='*.py')
    unittest.TextTestRunner().run(all_tests)

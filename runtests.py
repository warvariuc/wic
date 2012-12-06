#!/usr/bin/python3

if __name__ == "__main__":
    import unittest
    all_tests = unittest.TestLoader().discover('orm')
    unittest.TextTestRunner(verbosity=2).run(all_tests)

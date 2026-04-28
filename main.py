import lexer
import parser

def main():
    test_code = '''
      PROGRAM HELLO
      PRINT *, 'Ola, Mundo!'
      END
'''
    result = parser.parse(test_code)
    print(result)
from rply import LexerGenerator


class LexerOriginalConditionString:
    @classmethod
    def get_lexer(cls):
        lg = LexerGenerator()
        lg.add("ddr", r'ddr\(D\d{1,3}\)')
        lg.add("ddo", r'ddo\(D\d{1,3}\)')
        lg.add("ngp", r'ngp\(D\d{1,3}\)')
        lg.add("fctg", r'fctg\(G\d+\)\s*([<>]=?|==)\s*(\d+)')
        lg.add('mr', r'mr\(G\d{1,3}\)')
        lg.ignore(r'not|or|and|[\s+\(\)]')
        return lg


class LexerValuesInConditionString:

    @classmethod
    def get_lexer(cls):
        lg = LexerGenerator()
        lg.add("L_PAREN", r'\(')
        lg.add("R_PAREN", r'\)')
        lg.add("PLUS", r"\+")
        lg.add("MUL", r'\*')
        lg.add('NUM', r'\d+')
        lg.add('NOT', r'not')
        lg.ignore(r'\s+')
        return lg

def parse_operation_params(args: list[str] = []) -> [str, int, int, int, bool]:
    level = None
    times = -1
    potion = 0
    originite = 0
    eliminate = False

    try:
        for p in args:
            if p[0] == '-':
                val = -1
                if len(p) > 2:
                    val = int(p[2:])
                if p[1] == 'r':
                    assert potion == 0
                    potion = val
                elif p[1] == 'R':
                    assert originite == 0
                    originite = val
                elif p[1] == 'e':
                    assert not eliminate
                    eliminate = True
            elif p.find('-') == -1:
                assert times == -1
                times = int(p)
            else:
                assert level is None
                level = p
    except Exception:
        raise ParamError
    return [level, times, potion, originite, eliminate]


def operation_times(args: list[str] = []) -> int:
    _, times, _, _, _ = parse_operation_params(args)
    return times


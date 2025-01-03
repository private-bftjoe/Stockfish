import argparse
import re
import sys
import subprocess
import pathlib
import os

from testing import (
    EPD,
    TSAN,
    Stockfish as Engine,
    MiniTestFramework,
    OrderedClassMembers,
    Valgrind
)

PATH = pathlib.Path(__file__).parent.resolve()
CWD = os.getcwd()


def get_prefix():
    if args.valgrind:
        return Valgrind.get_valgrind_command()
    if args.valgrind_thread:
        return Valgrind.get_valgrind_thread_command()

    return []


def get_threads():
    if args.valgrind_thread or args.sanitizer_thread:
        return 2
    return 1


def get_path():
    return os.path.abspath(os.path.join(CWD, args.stockfish_path))


def postfix_check(output):
    if args.sanitizer_undefined:
        for idx, line in enumerate(output):
            if "runtime error:" in line:
                # print next possible 50 lines
                for i in range(50):
                    debug_idx = idx + i
                    if debug_idx < len(output):
                        print(output[debug_idx])
                return False

    if args.sanitizer_thread:
        for idx, line in enumerate(output):
            if "WARNING: ThreadSanitizer:" in line:
                # print next possible 50 lines
                for i in range(50):
                    debug_idx = idx + i
                    if debug_idx < len(output):
                        print(output[debug_idx])
                return False

    return True


def Stockfish(*args, **kwargs):
    return Engine(get_prefix(), get_path(), *args, **kwargs)


class TestCLI(metaclass=OrderedClassMembers):

    def beforeAll(self):
        pass

    def afterAll(self):
        pass

    def beforeEach(self):
        self.stockfish = None

    def afterEach(self):
        assert postfix_check(self.stockfish.get_output()) == True
        self.stockfish.clear_output()

    def test_eval(self):
        self.stockfish = Stockfish("eval".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_nodes_1000(self):
        self.stockfish = Stockfish("go nodes 1000".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_depth_10(self):
        self.stockfish = Stockfish("go depth 10".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_perft_4(self):
        self.stockfish = Stockfish("go perft 4".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_movetime_1000(self):
        self.stockfish = Stockfish("go movetime 1000".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_wtime_8000_btime_8000_winc_500_binc_500(self):
        self.stockfish = Stockfish(
            "go wtime 8000 btime 8000 winc 500 binc 500".split(" "),
            True,
        )
        assert self.stockfish.process.returncode == 0

    def test_go_wtime_1000_btime_1000_winc_0_binc_0(self):
        self.stockfish = Stockfish(
            "go wtime 1000 btime 1000 winc 0 binc 0".split(" "),
            True,
        )
        assert self.stockfish.process.returncode == 0

    def test_go_wtime_1000_btime_1000_winc_0_binc_0_movestogo_5(self):
        self.stockfish = Stockfish(
            "go wtime 1000 btime 1000 winc 0 binc 0 movestogo 5".split(" "),
            True,
        )
        assert self.stockfish.process.returncode == 0

    def test_go_movetime_200(self):
        self.stockfish = Stockfish("go movetime 200".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_go_nodes_20000_searchmoves_e2e4_d2d4(self):
        self.stockfish = Stockfish(
            "go nodes 20000 searchmoves e2e4 d2d4".split(" "), True
        )
        assert self.stockfish.process.returncode == 0

    def test_bench_128_threads_8_default_depth(self):
        self.stockfish = Stockfish(
            f"bench 128 {get_threads()} 8 default depth".split(" "),
            True,
        )
        assert self.stockfish.process.returncode == 0

    def test_bench_128_threads_3_bench_tmp_epd_depth(self):
        self.stockfish = Stockfish(
            f"bench 128 {get_threads()} 3 {os.path.join(PATH,'bench_tmp.epd')} depth".split(
                " "
            ),
            True,
        )
        assert self.stockfish.process.returncode == 0

    def test_d(self):
        self.stockfish = Stockfish("d".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_compiler(self):
        self.stockfish = Stockfish("compiler".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_license(self):
        self.stockfish = Stockfish("license".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_uci(self):
        self.stockfish = Stockfish("uci".split(" "), True)
        assert self.stockfish.process.returncode == 0

    def test_export_net_verify_nnue(self):
        current_path = os.path.abspath(os.getcwd())
        self.stockfish = Stockfish(
            f"export_net {os.path.join(current_path , 'verify.nnue')}".split(" "), True
        )
        assert self.stockfish.process.returncode == 0

    # verify the generated net equals the base net

    def test_network_equals_base(self):
        self.stockfish = Stockfish(
            ["uci"],
            True,
        )

        output = self.stockfish.process.stdout

        # find line
        for line in output.split("\n"):
            if "option name EvalFile type string default" in line:
                network = line.split(" ")[-1]
                break

        # find network file in src dir
        network = os.path.join(PATH.parent.resolve(), "src", network)

        if not os.path.exists(network):
            print(
                f"Network file {network} not found, please download the network file over the make command."
            )
            assert False

        diff = subprocess.run(["diff", network, f"verify.nnue"])

        assert diff.returncode == 0


class TestInteractive(metaclass=OrderedClassMembers):
    def beforeAll(self):
        self.stockfish = Stockfish()

    def afterAll(self):
        self.stockfish.quit()
        assert self.stockfish.close() == 0

    def afterEach(self):
        assert postfix_check(self.stockfish.get_output()) == True
        self.stockfish.clear_output()

    def test_startup_output(self):
        self.stockfish.starts_with("Stockfish")

    def test_uci_command(self):
        self.stockfish.send_command("uci")
        self.stockfish.equals("uciok")

    def test_set_threads_option(self):
        self.stockfish.send_command(f"setoption name Threads value {get_threads()}")

    def test_ucinewgame_and_startpos_nodes_1000(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("position startpos")
        self.stockfish.send_command("go nodes 1000")
        self.stockfish.starts_with("bestmove")

    def test_ucinewgame_and_startpos_moves(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("position startpos moves e2e4 e7e6")
        self.stockfish.send_command("go nodes 1000")
        self.stockfish.starts_with("bestmove")

    def test_fen_position_1(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("position fen 5rk1/1K4p1/8/8/3B4/8/8/8 b - - 0 1")
        self.stockfish.send_command("go nodes 1000")
        self.stockfish.starts_with("bestmove")

    def test_fen_position_2_flip(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("position fen 5rk1/1K4p1/8/8/3B4/8/8/8 b - - 0 1")
        self.stockfish.send_command("flip")
        self.stockfish.send_command("go nodes 1000")
        self.stockfish.starts_with("bestmove")

    def test_depth_5_with_callback(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("position startpos")
        self.stockfish.send_command("go depth 5")

        def callback(output):
            regex = r"info depth \d+ multipv \d+ score cp \d+ nodes \d+ nps \d+ hashfull \d+ time \d+ pv"
            if output.startswith("info depth") and not re.match(regex, output):
                assert False
            if output.startswith("bestmove"):
                return True
            return False

        self.stockfish.check_output(callback)

    def test_ucinewgame_and_go_depth_9(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command("setoption name UCI_ShowWDL value true")
        self.stockfish.send_command("position startpos")
        self.stockfish.send_command("go depth 9")

        depth = 1

        def callback(output):
            nonlocal depth

            regex = rf"info depth {depth} multipv \d+ score cp \d+ wdl \d+ \d+ \d+ nodes \d+ nps \d+ hashfull \d+ time \d+ pv"

            if output.startswith("info depth"):
                if not re.match(regex, output):
                    assert False
                depth += 1

            if output.startswith("bestmove"):
                assert depth == 10
                return True

            return False

        self.stockfish.check_output(callback)

    def test_fen_position_mate_1(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 5K2/8/2qk4/2nPp3/3r4/6B1/B7/3R4 w - e6"
        )
        self.stockfish.send_command("go depth 18")

        self.stockfish.expect("* score mate 1 * pv d5e6")
        self.stockfish.equals("bestmove d5e6")

    def test_fen_position_mate_minus_1(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 2brrb2/8/p7/Q7/1p1kpPp1/1P1pN1K1/3P4/8 b - -"
        )
        self.stockfish.send_command("go depth 18")
        self.stockfish.expect("* score mate -1 *")
        self.stockfish.starts_with("bestmove")

    def test_fen_position_fixed_node(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 5K2/8/2P1P1Pk/6pP/3p2P1/1P6/3P4/8 w - - 0 1"
        )
        self.stockfish.send_command("go nodes 500000")
        self.stockfish.starts_with("bestmove")

    def test_fen_position_with_mate_go_depth(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - -"
        )
        self.stockfish.send_command("go depth 18 searchmoves c6d7")
        self.stockfish.expect("* score mate 2 * pv c6d7 * f7f5")

        self.stockfish.starts_with("bestmove")

    def test_fen_position_with_mate_go_mate(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - -"
        )
        self.stockfish.send_command("go mate 2 searchmoves c6d7")
        self.stockfish.expect("* score mate 2 * pv c6d7 *")

        self.stockfish.starts_with("bestmove")

    def test_fen_position_with_mate_go_nodes(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - -"
        )
        self.stockfish.send_command("go nodes 500000 searchmoves c6d7")
        self.stockfish.expect("* score mate 2 * pv c6d7 * f7f5")

        self.stockfish.starts_with("bestmove")

    def test_fen_position_depth_27(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen r1b2r1k/pp1p2pp/2p5/2B1q3/8/8/P1PN2PP/R4RK1 w - - 0 18"
        )
        self.stockfish.send_command("go")
        self.stockfish.contains("score mate 1")

        self.stockfish.starts_with("bestmove")

    def test_fen_position_with_mate_go_depth_and_promotion(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - - moves c6d7 f2f1q"
        )
        self.stockfish.send_command("go depth 18")
        self.stockfish.expect("* score mate 1 * pv f7f5")
        self.stockfish.starts_with("bestmove f7f5")

    def test_fen_position_with_mate_go_depth_and_searchmoves(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - -"
        )
        self.stockfish.send_command("go depth 18 searchmoves c6d7")
        self.stockfish.expect("* score mate 2 * pv c6d7 * f7f5")

        self.stockfish.starts_with("bestmove c6d7")

    def test_fen_position_with_moves_with_mate_go_depth_and_searchmoves(self):
        self.stockfish.send_command("ucinewgame")
        self.stockfish.send_command(
            "position fen 8/5R2/2K1P3/4k3/8/b1PPpp1B/5p2/8 w - - moves c6d7"
        )
        self.stockfish.send_command("go depth 18 searchmoves e3e2")
        self.stockfish.expect("* score mate -1 * pv e3e2 f7f5")
        self.stockfish.starts_with("bestmove e3e2")

    def test_verify_nnue_network(self):
        current_path = os.path.abspath(os.getcwd())
        Stockfish(
            f"export_net {os.path.join(current_path , 'verify.nnue')}".split(" "), True
        )

        self.stockfish.send_command("setoption name EvalFile value verify.nnue")
        self.stockfish.send_command("position startpos")
        self.stockfish.send_command("go depth 5")
        self.stockfish.starts_with("bestmove")


def parse_args():
    parser = argparse.ArgumentParser(description="Run Stockfish with testing options")
    parser.add_argument("--valgrind", action="store_true", help="Run valgrind testing")
    parser.add_argument(
        "--valgrind-thread", action="store_true", help="Run valgrind-thread testing"
    )
    parser.add_argument(
        "--sanitizer-undefined",
        action="store_true",
        help="Run sanitizer-undefined testing",
    )
    parser.add_argument(
        "--sanitizer-thread", action="store_true", help="Run sanitizer-thread testing"
    )

    parser.add_argument(
        "--none", action="store_true", help="Run without any testing options"
    )
    parser.add_argument("stockfish_path", type=str, help="Path to Stockfish binary")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    EPD.create_bench_epd()
    TSAN.set_tsan_option()

    framework = MiniTestFramework()

    # Each test suite will be ran inside a temporary directory
    framework.run([TestCLI, TestInteractive])

    EPD.delete_bench_epd()
    TSAN.unset_tsan_option()

    if framework.has_failed():
        sys.exit(1)

    sys.exit(0)

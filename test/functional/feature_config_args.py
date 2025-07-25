# Copyright (c) 2017-2019 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test various command line arguments and configuration file parameters."""
import os
import pathlib
import re
import sys
import tempfile
import time

from test_framework.test_framework import BitcoinTestFramework
from test_framework.test_node import ErrorMatch
from test_framework.util import assert_equal, get_temp_default_datadir, write_config


class ConfArgsTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 1
        self.supports_cli = False
        self.wallet_names = []
        self.disable_autoconnect = False

    def test_config_file_parser(self):
        self.stop_node(0)

        inc_conf_file_path = os.path.join(self.nodes[0].datadir, "include.conf")
        with open(
            os.path.join(self.nodes[0].datadir, "bitcoin.conf"), "a", encoding="utf-8"
        ) as conf:
            conf.write(f"includeconf={inc_conf_file_path}\n")

        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error parsing command line arguments: Invalid parameter"
                " -dash_cli=1"
            ),
            extra_args=["-dash_cli=1"],
        )
        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("dash_conf=1\n")
        with self.nodes[0].assert_debug_log(
            expected_msgs=["Ignoring unknown configuration value dash_conf"]
        ):
            self.start_node(0)
        self.stop_node(0)

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("-dash=1\n")
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error reading configuration file: parse error on line 1:"
                " -dash=1, options in configuration file must be specified without"
                " leading -"
            )
        )

        if self.is_wallet_compiled():
            with open(inc_conf_file_path, "w", encoding="utf8") as conf:
                conf.write("wallet=foo\n")
            self.nodes[0].assert_start_raises_init_error(
                expected_msg=(
                    "Error: Config setting for -wallet only applied on"
                    f" {self.chain} network when in [{self.chain}] section."
                )
            )

        main_conf_file_path = os.path.join(
            self.options.tmpdir, "node0", "bitcoin_main.conf"
        )
        write_config(
            main_conf_file_path,
            n=0,
            chain="",
            extra_config=f"includeconf={inc_conf_file_path}\n",
        )
        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("acceptnonstdtxn=1\n")
        self.nodes[0].assert_start_raises_init_error(
            extra_args=[f"-conf={main_conf_file_path}", "-allowignoredconf"],
            expected_msg="Error: acceptnonstdtxn is not currently supported for main chain",
        )

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("nono\n")
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error reading configuration file: parse error on line 1: nono,"
                " if you intended to specify a negated option, use nono=1 instead"
            )
        )

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("server=1\nrpcuser=someuser\nrpcpassword=some#pass")
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error reading configuration file: parse error on line 3, using"
                " # in rpcpassword can be ambiguous and should be avoided"
            )
        )

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("server=1\nrpcuser=someuser\nmain.rpcpassword=some#pass")
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error reading configuration file: parse error on line 3, using"
                " # in rpcpassword can be ambiguous and should be avoided"
            )
        )

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("server=1\nrpcuser=someuser\n[main]\nrpcpassword=some#pass")
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error reading configuration file: parse error on line 4, using"
                " # in rpcpassword can be ambiguous and should be avoided"
            )
        )

        inc_conf_file2_path = os.path.join(self.nodes[0].datadir, "include2.conf")
        with open(
            os.path.join(self.nodes[0].datadir, "bitcoin.conf"), "a", encoding="utf-8"
        ) as conf:
            conf.write(f"includeconf={inc_conf_file2_path}\n")

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("testnot.datadir=1\n")
        with open(inc_conf_file2_path, "w", encoding="utf-8") as conf:
            conf.write("[testnet]\n")
        self.restart_node(0)
        self.nodes[0].stop_node(
            expected_stderr="Warning: "
            + inc_conf_file_path
            + ":1 Section [testnot] is not recognized."
            + os.linesep
            + inc_conf_file2_path
            + ":1 Section [testnet] is not recognized."
        )

        with open(inc_conf_file_path, "w", encoding="utf-8") as conf:
            conf.write("")  # clear
        with open(inc_conf_file2_path, "w", encoding="utf-8") as conf:
            conf.write("")  # clear

    def test_invalid_command_line_options(self):
        self.nodes[0].assert_start_raises_init_error(
            expected_msg=(
                "Error: Error parsing command line arguments: Can not set -proxy "
                "with no value. Please specify value with -proxy=value."
            ),
            extra_args=["-proxy"],
        )

    def test_log_buffer(self):
        self.stop_node(0)
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Warning: parsed potentially confusing double-negative -connect=0\n"
            ]
        ):
            self.start_node(0, extra_args=["-noconnect=0"])

    def test_args_log(self):
        self.stop_node(0)
        self.log.info("Test config args logging")
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                'Command-line arg: addnode="some.node"',
                "Command-line arg: rpcauth=****",
                "Command-line arg: rpcbind=****",
                "Command-line arg: rpcpassword=****",
                "Command-line arg: rpcuser=****",
                "Command-line arg: torpassword=****",
                f'Config file arg: {self.chain}="1"',
                f'Config file arg: [{self.chain}] server="1"',
            ],
            unexpected_msgs=[
                "alice:f7efda5c189b999524f151318c0c86$d5b51b3beffbc0",
                "127.1.1.1",
                "secret-rpcuser",
                "secret-torpassword",
            ],
        ):
            self.start_node(
                0,
                extra_args=[
                    "-addnode=some.node",
                    "-rpcauth=alice:f7efda5c189b999524f151318c0c86$d5b51b3beffbc0",
                    "-rpcbind=127.1.1.1",
                    "-rpcpassword=",
                    "-rpcuser=secret-rpcuser",
                    "-torpassword=secret-torpassword",
                ],
            )

    def test_networkactive(self):
        self.log.info("Test -networkactive option")
        self.stop_node(0)
        with self.nodes[0].assert_debug_log(expected_msgs=["SetNetworkActive: true\n"]):
            self.start_node(0)

        self.stop_node(0)
        with self.nodes[0].assert_debug_log(expected_msgs=["SetNetworkActive: true\n"]):
            self.start_node(0, extra_args=["-networkactive"])

        self.stop_node(0)
        with self.nodes[0].assert_debug_log(expected_msgs=["SetNetworkActive: true\n"]):
            self.start_node(0, extra_args=["-networkactive=1"])

        self.stop_node(0)
        with self.nodes[0].assert_debug_log(
            expected_msgs=["SetNetworkActive: false\n"]
        ):
            self.start_node(0, extra_args=["-networkactive=0"])

        self.stop_node(0)
        with self.nodes[0].assert_debug_log(
            expected_msgs=["SetNetworkActive: false\n"]
        ):
            self.start_node(0, extra_args=["-nonetworkactive"])

        self.stop_node(0)
        with self.nodes[0].assert_debug_log(
            expected_msgs=["SetNetworkActive: false\n"]
        ):
            self.start_node(0, extra_args=["-nonetworkactive=1"])

    def test_seed_peers(self):
        self.log.info("Test seed peers")
        default_data_dir = self.nodes[0].datadir
        # Only regtest has no fixed seeds. To avoid connections to random
        # nodes, regtest is the only network where it is safe to enable
        # -fixedseeds in tests
        assert_equal(self.nodes[0].getblockchaininfo()["chain"], "regtest")
        self.stop_node(0)

        # No peers.dat exists and -dnsseed=1
        # We expect the node will use DNS Seeds, but Regtest mode has 0 DNS seeds
        # So after 60 seconds, the node should fallback to fixed seeds (this is
        # a slow test)
        assert not os.path.exists(os.path.join(default_data_dir, "peers.dat"))
        start = int(time.time())
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Loaded 0 addresses from peers.dat",
                "0 addresses found from DNS seeds",
                "opencon thread start",
            ],
            timeout=10,
        ):
            self.start_node(
                0, extra_args=["-dnsseed=1", "-fixedseeds=1", f"-mocktime={start}"]
            )
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Adding fixed seeds as 60 seconds have passed and addrman is empty",
            ]
        ):
            self.nodes[0].setmocktime(start + 65)
        self.stop_node(0)

        # No peers.dat exists and -dnsseed=0
        # We expect the node will fallback immediately to fixed seeds
        assert not os.path.exists(os.path.join(default_data_dir, "peers.dat"))
        start = time.time()
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Loaded 0 addresses from peers.dat",
                "DNS seeding disabled",
                (
                    "Adding fixed seeds as -dnsseed=0 and neither -addnode nor "
                    "-seednode are provided\n"
                ),
            ],
            timeout=10,
        ):
            self.start_node(0, extra_args=["-dnsseed=0", "-fixedseeds=1"])
        assert time.time() - start < 60
        self.stop_node(0)

        # No peers.dat exists and dns seeds are disabled.
        # We expect the node will not add fixed seeds when explicitly disabled.
        assert not os.path.exists(os.path.join(default_data_dir, "peers.dat"))
        start = time.time()
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Loaded 0 addresses from peers.dat",
                "DNS seeding disabled",
                "Fixed seeds are disabled",
            ],
            timeout=10,
        ):
            self.start_node(0, extra_args=["-dnsseed=0", "-fixedseeds=0"])
        assert time.time() - start < 60
        self.stop_node(0)

        # No peers.dat exists and -dnsseed=0, but a -addnode is provided
        # We expect the node will allow 60 seconds prior to using fixed seeds
        assert not os.path.exists(os.path.join(default_data_dir, "peers.dat"))
        start = int(time.time())
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Loaded 0 addresses from peers.dat",
                "DNS seeding disabled",
                "opencon thread start",
            ],
            timeout=10,
        ):
            self.start_node(
                0,
                extra_args=[
                    "-dnsseed=0",
                    "-fixedseeds=1",
                    "-addnode=fakenodeaddr",
                    f"-mocktime={start}",
                ],
            )
        with self.nodes[0].assert_debug_log(
            expected_msgs=[
                "Adding fixed seeds as 60 seconds have passed and addrman is empty",
            ]
        ):
            self.nodes[0].setmocktime(start + 65)

    def test_ignored_conf(self):
        self.log.info(
            "Test error is triggered when the datadir in use contains a bitcoin.conf file that would be ignored "
            "because a conflicting -conf file argument is passed."
        )
        node = self.nodes[0]
        with tempfile.NamedTemporaryFile(
            dir=self.options.tmpdir, mode="wt", delete=False
        ) as temp_conf:
            temp_conf.write(f"datadir={node.datadir}\n")
        node.assert_start_raises_init_error(
            [f"-conf={temp_conf.name}"],
            re.escape(
                f'Error: Data directory "{node.datadir}" contains a "bitcoin.conf" file which is ignored, because a '
                f'different configuration file "{temp_conf.name}" from command line argument "-conf={temp_conf.name}" '
                f"is being used instead."
            )
            + r"[\s\S]*",
            match=ErrorMatch.FULL_REGEX,
        )

        # Test that passing a redundant -conf command line argument pointing to
        # the same bitcoin.conf that would be loaded anyway does not trigger an
        # error.
        self.start_node(0, [f"-conf={node.datadir}/bitcoin.conf"])
        self.stop_node(0)

    def test_ignored_default_conf(self):
        # Disable this test for windows currently because trying to override
        # the default datadir through the environment does not seem to work.
        if sys.platform == "win32":
            return

        self.log.info(
            "Test error is triggered when bitcoin.conf in the default data directory sets another datadir "
            "and it contains a different bitcoin.conf file that would be ignored"
        )

        # Create a temporary directory that will be treated as the default data
        # directory by bitcoind.
        env, default_datadir = get_temp_default_datadir(
            pathlib.Path(self.options.tmpdir, "home")
        )
        default_datadir.mkdir(parents=True)

        # Write a bitcoin.conf file in the default data directory containing a
        # datadir= line pointing at the node datadir. This will trigger a
        # startup error because the node datadir contains a different
        # bitcoin.conf that would be ignored.
        node = self.nodes[0]
        (default_datadir / "bitcoin.conf").write_text(f"datadir={node.datadir}\n")

        # Drop the node -datadir= argument during this test, because if it is
        # specified it would take precedence over the datadir setting in the
        # config file.
        node_default_args = node.default_args
        node.default_args = [
            arg for arg in node.default_args if not arg.startswith("-datadir=")
        ]
        node.assert_start_raises_init_error(
            [],
            re.escape(
                f'Error: Data directory "{node.datadir}" contains a "bitcoin.conf" file which is ignored, because a '
                f'different configuration file "{default_datadir}/bitcoin.conf" from data directory "{default_datadir}" '
                f"is being used instead."
            )
            + r"[\s\S]*",
            env=env,
            match=ErrorMatch.FULL_REGEX,
        )
        node.default_args = node_default_args

    def run_test(self):
        self.test_log_buffer()
        self.test_args_log()
        self.test_seed_peers()
        self.test_networkactive()

        self.test_config_file_parser()
        self.test_invalid_command_line_options()
        self.test_ignored_conf()
        self.test_ignored_default_conf()

        # Remove the -datadir argument so it doesn't override the config file
        self.nodes[0].remove_default_args(["-datadir"])

        default_data_dir = self.nodes[0].datadir
        new_data_dir = os.path.join(default_data_dir, "newdatadir")
        new_data_dir_2 = os.path.join(default_data_dir, "newdatadir2")

        # Check that using -datadir argument on non-existent directory fails
        self.nodes[0].datadir = new_data_dir
        self.nodes[0].assert_start_raises_init_error(
            [f"-datadir={new_data_dir}"],
            f'Error: Specified data directory "{new_data_dir}" does not exist.',
        )

        # Check that using non-existent datadir in conf file fails
        conf_file = os.path.join(default_data_dir, "bitcoin.conf")

        # datadir needs to be set before [chain] section
        conf_file_contents = open(conf_file, encoding="utf8").read()
        with open(conf_file, "w", encoding="utf8") as f:
            f.write(f"datadir={new_data_dir}\n")
            f.write(conf_file_contents)

        self.nodes[0].assert_start_raises_init_error(
            [f"-conf={conf_file}"],
            "Error: Error reading configuration file: specified data directory"
            f' "{new_data_dir}" does not exist.',
        )

        # Create the directory and ensure the config file now works
        os.mkdir(new_data_dir)
        self.start_node(0, [f"-conf={conf_file}"])
        self.stop_node(0)
        assert os.path.exists(os.path.join(new_data_dir, self.chain, "blocks"))

        # Ensure command line argument overrides datadir in conf
        os.mkdir(new_data_dir_2)
        self.nodes[0].datadir = new_data_dir_2
        self.start_node(0, [f"-datadir={new_data_dir_2}", f"-conf={conf_file}"])
        assert os.path.exists(os.path.join(new_data_dir_2, self.chain, "blocks"))


if __name__ == "__main__":
    ConfArgsTest().main()

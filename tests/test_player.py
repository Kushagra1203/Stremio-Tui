import unittest
import urllib.parse
from unittest import mock

from core import player


class CheckPlayerDependenciesTests(unittest.TestCase):
    @mock.patch("core.player.shutil.which", return_value="/usr/bin/webtorrent")
    def test_both_present_does_not_raise(self, which):
        which.side_effect = lambda b: f"/usr/bin/{b}"
        player.check_player_dependencies()
        self.assertEqual(which.call_count, 2)

    @mock.patch("core.player.shutil.which", return_value=None)
    def test_missing_webtorrent_names_the_binary_and_the_fix(self, which):
        with self.assertRaises(player.PlayerUnavailable) as ctx:
            player.check_player_dependencies()

        message = str(ctx.exception)
        self.assertIn("webtorrent", message)
        self.assertIn("npm install -g webtorrent-cli", message)

    @mock.patch("core.player.shutil.which")
    def test_missing_mpv_is_reported_separately(self, which):
        # webtorrent present, mpv absent -- the second check is what must fail.
        which.side_effect = lambda b: "/usr/bin/webtorrent" if b == "webtorrent" else None

        with self.assertRaises(player.PlayerUnavailable) as ctx:
            player.check_player_dependencies()

        self.assertIn("mpv", str(ctx.exception))

    @mock.patch("core.player.shutil.which", return_value=None)
    @mock.patch("core.player.subprocess.run")
    def test_play_stream_does_not_spawn_anything_when_deps_are_missing(
        self, run, which
    ):
        with self.assertRaises(player.PlayerUnavailable):
            player.play_stream("magnet:?xt=urn:btih:deadbeef")

        run.assert_not_called()


class BuildMagnetTests(unittest.TestCase):
    def query(self, magnet):
        return urllib.parse.parse_qs(urllib.parse.urlparse(magnet).query)

    def test_magnet_carries_the_info_hash_and_a_tracker_list(self):
        magnet = player.build_magnet("Some Show", "abc123")

        params = self.query(magnet)
        self.assertEqual(params["xt"], ["urn:btih:abc123"])
        self.assertEqual(params["dn"], ["Some Show"])
        # A magnet with no trackers can never find peers.
        self.assertGreater(len(params["tr"]), 1)

    def test_the_xt_parameter_is_not_percent_encoded(self):
        # webtorrent 3.x answers a magnet whose `xt` is encoded with
        # "Invalid torrent identifier" and refuses to play it, so the colons
        # in `urn:btih:` must stay literal.
        magnet = player.build_magnet("Some Show", "abc123")

        self.assertIn("xt=urn:btih:abc123", magnet)
        self.assertNotIn("xt=urn%3A", magnet)

    def test_display_name_is_stripped_of_newlines_and_truncated(self):
        magnet = player.build_magnet("The Show\nS01E01 1080p", "abc123")

        name = self.query(magnet)["dn"][0]
        self.assertNotIn("\n", name)
        self.assertLessEqual(len(name), 120)

    def test_addon_supplied_trackers_are_kept_alongside_the_defaults(self):
        magnet = player.build_magnet(
            "Show", "abc123", sources=["tracker:udp://custom.example:1337/announce"]
        )

        trackers = self.query(magnet)["tr"]
        self.assertIn("udp://custom.example:1337/announce", trackers)
        self.assertGreater(len(trackers), 1)

    def test_duplicate_trackers_are_not_added_twice(self):
        magnet = player.build_magnet(
            "Show", "abc123", trackers=["udp://one/announce"], sources=["tracker:udp://one/announce"]
        )

        self.assertEqual(self.query(magnet)["tr"], ["udp://one/announce"])

    def test_missing_name_is_allowed(self):
        magnet = player.build_magnet("", "abc123")

        self.assertNotIn("dn", self.query(magnet))


class ResolveStreamLinkTests(unittest.TestCase):
    def test_a_ready_url_is_used_as_is(self):
        stream = {"url": "https://example.com/file.torrent"}

        self.assertEqual(player.resolve_stream_link(stream), "https://example.com/file.torrent")

    def test_a_bare_info_hash_becomes_a_magnet_with_trackers(self):
        stream = {"infoHash": "abc123", "title": "Some Show"}

        magnet = player.resolve_stream_link(stream)

        self.assertTrue(magnet.startswith("magnet:?"))
        self.assertIn("xt=urn:btih:abc123", magnet)
        self.assertIn("tr=", magnet)

    def test_a_stream_with_neither_url_nor_hash_is_rejected(self):
        with self.assertRaises(player.PlayerUnavailable):
            player.resolve_stream_link({"title": "Some Show"})


class BuildCommandTests(unittest.TestCase):
    def test_command_passes_the_link_and_a_download_dir(self):
        cmd = player.build_command("magnet:?xt=urn:btih:abc", "/tmp/out")

        self.assertEqual(cmd[0], "webtorrent")
        self.assertIn("magnet:?xt=urn:btih:abc", cmd)
        self.assertEqual(cmd[cmd.index("--out") + 1], "/tmp/out")
        self.assertIn("--mpv", cmd)

    def test_player_args_are_a_single_token(self):
        # `--player-args=--save-position-on-quit` must stay one argv entry;
        # splitting it would make webtorrent treat the flag as a filename.
        cmd = player.build_command("link", "/tmp/out")

        player_args = [c for c in cmd if c.startswith("--player-args=")]
        self.assertEqual(len(player_args), 1)
        self.assertEqual(player_args[0], f"--player-args={player.PLAYER_ARGS}")

    def test_file_index_is_passed_as_select(self):
        cmd = player.build_command("link", "/tmp/out", select=3)

        self.assertEqual(cmd[cmd.index("--select") + 1], "3")

    def test_file_index_is_omitted_when_unknown(self):
        cmd = player.build_command("link", "/tmp/out")

        self.assertNotIn("--select", cmd)


if __name__ == "__main__":
    unittest.main()

import unittest
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


if __name__ == "__main__":
    unittest.main()

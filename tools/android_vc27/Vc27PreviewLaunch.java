package com.godot.game;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** Launcher for the labelled preview profile. Not the normal game icon. */
public class Vc27PreviewLaunch extends Activity {
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		Intent game = new Intent(this, Vc27PreviewApp.class);
		game.putExtra("command_line_params", new String[] {"--", "--vc27-preview"});
		game.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
		startActivity(game);
		finish();
	}
}

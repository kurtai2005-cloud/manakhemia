package com.godot.game;

import java.util.ArrayList;
import java.util.List;

/**
 * Preview icon only. Always passes --vc27-preview, including when Recents or a
 * process restart arrives without the launcher extra. The normal icon stays GodotApp.
 */
public class Vc27PreviewApp extends GodotApp {
	@Override
	public List<String> getCommandLine() {
		List<String> incoming = super.getCommandLine();
		ArrayList<String> params = new ArrayList<>();
		if (incoming != null) {
			params.addAll(incoming);
		}
		boolean flag = false;
		boolean sep = false;
		for (String p : params) {
			if ("--vc27-preview".equals(p)) {
				flag = true;
			}
			if ("--".equals(p)) {
				sep = true;
			}
		}
		if (!flag) {
			if (!sep) {
				params.add("--");
			}
			params.add("--vc27-preview");
		}
		return params;
	}
}

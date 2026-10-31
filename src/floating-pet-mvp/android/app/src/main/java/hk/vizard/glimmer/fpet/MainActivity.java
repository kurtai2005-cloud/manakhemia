package hk.vizard.glimmer.fpet;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.TextView;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(FloatingPetPlugin.class);
        super.onCreate(savedInstanceState);
        // 原生「浮動團絨」入口（右下角細掣），開設定頁
        float d = getResources().getDisplayMetrics().density;
        TextView b = new TextView(this);
        b.setText("🐾");
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        b.setGravity(Gravity.CENTER);
        b.setContentDescription("浮動團絨設定");
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.OVAL);
        bg.setColor(Color.argb(190, 255, 248, 235));
        bg.setStroke((int) (1.5f * d), Color.argb(200, 220, 180, 130));
        b.setBackground(bg);
        b.setAlpha(0.9f);
        b.setOnClickListener(v -> startActivity(new Intent(this, SettingsActivity.class)));
        int s = (int) (48 * d);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(s, s, Gravity.BOTTOM | Gravity.END);
        lp.setMargins(0, 0, (int) (10 * d), (int) (64 * d));
        addContentView(b, lp);
    }
}

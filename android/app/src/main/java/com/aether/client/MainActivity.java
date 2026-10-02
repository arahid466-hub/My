package com.aether.client;
import android.app.*; import android.os.*; import android.content.*; import android.view.*; import android.webkit.*; import android.widget.*;
public class MainActivity extends Activity {
  WebView web; String url;
  public void onCreate(Bundle b){super.onCreate(b); url=getPreferences(0).getString("server_url","http://10.0.2.2:8000"); web=new WebView(this); web.getSettings().setJavaScriptEnabled(true); web.setWebViewClient(new WebViewClient()); web.loadUrl(url); setContentView(web);}
  public boolean onCreateOptionsMenu(Menu m){m.add("Server URL"); return true;}
  public boolean onOptionsItemSelected(MenuItem i){ final EditText e=new EditText(this); e.setText(url); new AlertDialog.Builder(this).setTitle("Aether server URL").setView(e).setPositiveButton("Save",(d,w)->{url=e.getText().toString();getPreferences(0).edit().putString("server_url",url).apply();web.loadUrl(url);}).setNegativeButton("Cancel",null).show(); return true; }
}

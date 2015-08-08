package com.core321.stalk.stalk;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.os.Handler;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ListView;
import android.widget.SimpleAdapter;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import android.content.Intent;


public class MainActivity extends AppCompatActivity implements StalkAgentScanner.Listener {
    ListView listView;
    StalkAgentScanner scanner = new StalkAgentScanner();
    ArrayList<Map<String, String>> items = new ArrayList<Map<String, String>>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        listView = (ListView)findViewById(R.id.listView);

        SimpleAdapter adapter = new SimpleAdapter(this, items, android.R.layout.simple_list_item_2,
                new String[]{"title", "subtitle"},
                new int[] {android.R.id.text1, android.R.id.text2});

        listView.setAdapter(adapter);

        listView.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            @Override
            public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
                agentTapped(scanner.getAgents().get(position));
            }
        });

        //
        scanner.start(this);

        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                ///// TEST
                StalkAgent a = new StalkAgent();
                a.ipAddress = "naver.com";
                a.webUiPort = 80;
                a.hostName = "NAVER";
                agentTapped(a);
            }
        }, 1000 * 5);
    }

    @Override
    public void agentListChanged() {
        MainActivity.this.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                items.clear();
                for (StalkAgent agent : scanner.getAgents()) {
                    HashMap<String, String> ctx = new HashMap<String, String>();
                    ctx.put("title", agent.hostName);
                    ctx.put("subtitle", agent.ipAddress + ":" + agent.webUiPort);
                    items.add(ctx);
                }
                listView.invalidateViews();
            }
        });
    }

    void agentTapped(StalkAgent agent) {
        Intent intent = new Intent(MainActivity.this, WebViewActivity.class);
        Bundle b = new Bundle();
        b.putString("url", "http://" + agent.ipAddress + ":" + agent.webUiPort);
        b.putString("title", agent.hostName);
        intent.putExtras(b);
        startActivity(intent);

        overridePendingTransition(R.anim.slide_in_right, R.anim.slide_out_left);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }
}

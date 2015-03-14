// Charts view
//
// Derived from https://github.com/delan/lookout/

(function() {
    var latency = 0; // msec
    var wait = 2 * 1000; // msec
    var margin = 150; // msec
    var decimal = 0;

    var g = {}; // graphs
    var u = {}; // utility functions
    var h = {}; // data handlers

    // Utilities
    u.padt = function(s) {
        return ('00' + s).slice(-2);
    };
    u.seconds = function(n) {
        var d = Math.floor(n / 86400);
        var h = Math.floor(n / 3600) % 24;
        var m = Math.floor(n / 60) % 60;
        var s = Math.floor(n) % 60;
        return d + 'd ' + [u.padt(h), u.padt(m), u.padt(s)].join(':');
    };
    u.bytes = function(n) {
        var base = decimal ? 10 : 2;
        var exp = decimal ? 3 : 10;
        var units = decimal ? ['B', 'KB', 'MB', 'GB', 'TB', 'PB'] :
                              ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];
        for (i = 5; i >= 0; i--)
            if (n >= Math.pow(base, i * exp) - 1)
                return (n / Math.pow(base, i * exp)).toFixed(2) + ' ' + units[i];
    };
    u.percent = function(n) {
        return n.toFixed(1) + '%';
    };


    // Handlers
    h.engine = function(d) {
        $('#engine_id').text(d.engine_id);
        $('#engine_uptime').text(u.seconds(d.uptime));
        $('#rt_version').text(d.versions[0]);
        $('#lt_version').text(d.versions[1]);

        for (var i in d.views)
            $('#v_' + i).text(d.views[i]);

        $('#rtrs').text(u.bytes(d.download[0]) + '/s');
        $('#rtws').text(u.bytes(d.upload[0]) + '/s');
        if (d.download[1] > 0) $('#rtrs').prop('title', u.percent(100.0 * d.download[0] / d.download[1]));
        if (d.upload[1] > 0)   $('#rtws').prop('title', u.percent(100.0 * d.upload[0] / d.upload[1]));
        g.rtrs.t.append(+new Date, d.download[0] / 1048576); // MiB
        g.rtws.t.append(+new Date, d.upload[0] / 1048576); // MiB
    };
    h.uptime = function(d) {
        $('#uptime').text(u.seconds(d));
    };
    h.disk_usage = function(du) {
        var disku = [], diskt = [], diskp = [];
        for (var i = 0; i < du[2].length; i++) {
            var d = du[2][i];
            disku.push('<span class="value">' + u.bytes(d[0]) + '</span>');
            diskt.push('<span class="value">' + u.bytes(d[1]) + '</span>');
            diskp.push('<span class="value">' + u.percent(100.0 * d[0] / d[1]) + '</span>');
        }
        $('#disku').html(disku.join(" /&nbsp;"));
        $('#diskt').html(diskt.join(" /&nbsp;"));
        $('#diskp').html(diskp.join(" /&nbsp;"));
    };
    h.disk_io = function(d) {
        var now = new Date();
        var interval = (now.getTime() - (h.disk_io.lasttm || 0)) / 1000.0;
        
        $('#diskr').text(u.bytes(d[2]));
        $('#diskw').text(u.bytes(d[3]));
        if (h.disk_io.lastr != undefined) {
            var rs = (d[2] - (h.disk_io.lastr || 0)) / interval;
            var ws = (d[3] - (h.disk_io.lastw || 0)) / interval;
            $('#diskrs').text(u.bytes(rs) + '/s');
            $('#diskws').text(u.bytes(ws) + '/s');
            g.diskrs.t.append(+now, rs / 1048576); // MiB
            g.diskws.t.append(+now, ws / 1048576); // MiB
        }
        h.disk_io.lastr = d[2];
        h.disk_io.lastw = d[3];
        h.disk_io.lasttm = now.getTime();
    };
    h.net_io = function(d) {
        var now = new Date();
        var interval = (now.getTime() - (h.net_io.lasttm || 0)) / 1000.0;

        $('#netr').text(u.bytes(d[1]));
        $('#netw').text(u.bytes(d[0]));
        if (h.net_io.lastr != undefined) {
            var rs = (d[1] - (h.net_io.lastr || 0)) / interval;
            var ws = (d[0] - (h.net_io.lastw || 0)) / interval;
            $('#netrs').text(u.bytes(rs) + '/s');
            $('#netws').text(u.bytes(ws) + '/s');
            g.netrs.t.append(+now, rs / 1048576); // MiB
            g.netws.t.append(+now, ws / 1048576); // MiB
        }
        h.net_io.lastr = d[1];
        h.net_io.lastw = d[0];
        h.net_io.lasttm = now.getTime();
    };
    h.cpu_usage = function(d) {
        $('#cpu_usage').text(u.percent(d));
        g.cpu_usage.t.append(+new Date, d);
    };
    h.ram_usage = function(d) {
        $('#ram_usage').text(u.percent(d[2]));
        $('#ram_usage').prop('title', u.bytes(d[0] - d[1]));
        g.ram_usage.t.append(+new Date, d[2]);
    };
    h.swap_usage = function(d) {
        $('#swap_usage').text(u.percent(d[3]));
        $('#swap_usage').prop('title', u.bytes(d[1]));
        g.swap_usage.t.append(+new Date, d[3]);
    };
    function update(d) {
        if (d != undefined) {
            document.title = d.fqdn + ' - PyroScope Monitoring';
        }
        $('#latency').text(latency + ' ms');
        g.latency.t.append(+new Date, latency);
        $('#calls').text(calls);
        $('#errors').text(errors);
    }

    // Updating
    var calls = 0, errors = 0;

    function ping() {
        var time = +new Date;
        heartbeaton();
        $.get('/json/charts', function(data) {
            ++calls;
            $('#error_msg').parent().addClass('hidden');
            $('#last_updated').text(new Date(data.engine.now * 1000));

            // call data handlers
            for (var i in data)
                h[i] && data[i] != null && h[i](data[i]);

            // compensate for request time while allowing time for
            // the heartbeat transitions to complete
            var t = latency = new Date - time;
            update(data);

            if (t <= margin) {
                // call was faster than the CSS transition
                setTimeout(heartbeatoff, margin - t);
                setTimeout(ping, wait - t);
            } else if (t <= wait - margin) {
                heartbeatoff();
                setTimeout(ping, wait - t);
            } else {
                heartbeatoff();
                setTimeout(ping, margin);
            }
        });
    }
    function heartbeaton() {
        $('#heartbeat').addClass('on');
    }
    function heartbeatoff() {
        $('#heartbeat').removeClass('on');
    }
    function error(ev, xhr, settings, exc) {
        ++errors;
        ++calls;
        //$('#last_updated').text('OFFLINE');
        $('#error_msg').parent().removeClass('hidden');
        $('#error_msg').text('Cannot access ' + settings.url);
        console.log("AJAX error: ev = %o", ev);
        console.log("AJAX error: xhr = %o", xhr);
        console.log("AJAX error: settings = %o", settings);
        console.log("AJAX error: exc = %o", exc);
        update();
        heartbeatoff();
        setTimeout(ping, wait); // TODO: incremental back-off
    }
    $(document).on('ajaxError', error);
    $('#error_msg').siblings('a.close').on('click', function (e) {
        $(this).parent().addClass('hidden');
    });
    function graph(name, percentage) {
        var options = {
            millisPerPixel: wait,
            grid: {
                fillStyle: 'rgba(32, 32, 32, 1)',
                strokeStyle: 'rgba(0, 0, 0, 0)'
            },
        };
        
        if (percentage) {
            options.minValue = 0;
            options.maxValue = 100;
            options.labels = { fillStyle: 'rgba(0, 0, 0, 0)' };
        }

        var ts_options = {
            strokeStyle: 'rgba(255, 64, 64, 1)'
        };

        g[name] = {
            c: new SmoothieChart(options),
            t: new TimeSeries(),
        };
        g[name].c.streamTo($('#c_' + name)[0], 1000);
        g[name].c.addTimeSeries(g[name].t, ts_options);
    }
    // jQuery only
    //$.ajaxSetup({
    //  timeout: 5000,
    //  error: error
    //});
    var graphlist = {
        latency: 0,
        cpu_usage: 1,
        ram_usage: 1,
        swap_usage: 1,
        diskrs: 0,
        diskws: 0,
        netrs: 0,
        netws: 0,
        rtrs: 0,
        rtws: 0,
    };
    for (var i in graphlist)
        graph(i, graphlist[i]);
    ping();
})();

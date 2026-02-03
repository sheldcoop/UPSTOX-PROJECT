# 📊 Real-Time Monitoring Dashboard

## Overview

The UPSTOX Trading Platform now includes a **real-time monitoring dashboard** that provides live status updates, automatic log rotation, and auto-restart capabilities for all services.

## Features

### 🔄 Real-Time Monitoring
- **Live Status Updates**: Dashboard refreshes every 5 seconds automatically
- **Service Health Tracking**: Monitor API, OAuth, and Frontend services
- **Uptime Tracking**: See how long each service has been running
- **Restart Counter**: Track how many times services have been auto-restarted
- **Process Monitoring**: Background thread continuously checks service health

### 📝 Automatic Log Rotation
- **Size-Based Rotation**: Logs automatically rotate when they reach 10MB
- **Backup Management**: Keeps the last 5 log file backups
- **Timestamped Backups**: Rotated logs are saved with timestamps
- **Visual Indicators**: Dashboard shows log file sizes with color-coded warnings
  - 🟢 Green: < 50% of max size
  - 🟡 Yellow: 50-80% of max size
  - 🔴 Red: > 80% of max size

### 🔁 Auto-Restart
- **Crash Detection**: Automatically detects when services crash
- **Automatic Recovery**: Restarts crashed services immediately
- **Restart Tracking**: Counts and displays restart attempts
- **Zero Downtime**: Services are restarted without manual intervention

## Usage

### Starting with Dashboard (Default)

When you start the platform normally, it automatically launches the monitoring dashboard:

```bash
python3.11 run_platform.py
```

After all services start, the dashboard will launch automatically after a 3-second countdown.

### Dashboard-Only Mode

To view the dashboard for already running services without restarting them:

```bash
python3.11 run_platform.py --dashboard
```

This is useful when:
- Services are already running
- You want to monitor without interrupting services
- You closed the dashboard but services are still running

### Dashboard Controls

Once the dashboard is running, you can use these keyboard shortcuts:

- **`s`** - Refresh status immediately (force update)
- **`q`** - Quit dashboard (services keep running)
- **`Ctrl+C`** - Stop all services and exit

## Dashboard Layout

```
================================================================================
  📊 UPSTOX Trading Platform - Real-Time Status Dashboard
================================================================================

⏰ Current Time: 2026-02-03 20:45:23

────────────────────────────────────────────────────────────────────────────────
SERVICE              STATUS       UPTIME          RESTARTS   PORT    
────────────────────────────────────────────────────────────────────────────────
API Server           ● RUNNING    5m 23s          0          8000    
OAuth Server         ● RUNNING    5m 22s          0          5050    
Frontend Dashboard   ● RUNNING    5m 21s          0          5001    
────────────────────────────────────────────────────────────────────────────────

📝 Log Files:
   • API Server          0.15MB (1%)
   • OAuth Server        0.08MB (1%)
   • Frontend Dashboard  0.02MB (0%)

────────────────────────────────────────────────────────────────────────────────
💡 Press 's' for status, 'q' to quit, or Ctrl+C to stop all services
================================================================================
```

## Service Status Indicators

- **🟢 ● RUNNING** - Service is healthy and operational
- **🟡 ● STARTING** - Service is initializing
- **🔴 ● CRASHED** - Service has crashed (auto-restart in progress)
- **⚪ ● STOPPED** - Service is not running

## Log Rotation Details

### Configuration

Default settings (can be modified in `run_platform.py`):
- **Max Log Size**: 10MB per file
- **Backup Count**: 5 rotated files
- **Rotation Trigger**: Automatic when size limit is reached
- **Check Frequency**: Every 5 seconds (during monitoring)

### Log File Naming

When logs are rotated, they follow this naming pattern:

```
api_server.log                    # Current active log
api_server.20260203_204523.log   # Rotated backup (timestamp)
api_server.20260203_183015.log   # Older backup
...
```

### Manual Log Cleanup

Old log backups are automatically deleted when the backup count exceeds 5. You can also manually clean logs:

```bash
# Remove all rotated logs
rm logs/*.20*.log

# Remove all logs (be careful!)
rm logs/*.log
```

## Monitoring Thread Details

### How It Works

1. **Background Thread**: Runs in daemon mode, doesn't block main execution
2. **Check Interval**: Every 5 seconds
3. **Process Validation**: Uses `process.poll()` to check if services are alive
4. **Auto-Restart**: Immediately restarts crashed services
5. **Log Rotation**: Checks and rotates logs during each cycle

### Thread Safety

- Monitoring thread is daemon-based (exits when main program exits)
- Graceful shutdown on Ctrl+C or quit command
- No race conditions with service management

## Troubleshooting

### Dashboard Not Showing

If the dashboard doesn't appear:

1. **Check Terminal Compatibility**: Requires ANSI color support
2. **Verify Python Version**: Needs Python 3.11+
3. **Check Terminal Settings**: Must support `termios` (Unix-like systems)

### Services Keep Restarting

If you see high restart counts:

1. **Check Service Logs**: `tail -f logs/api_server.log`
2. **Verify Configuration**: Check `.env` file settings
3. **Review Dependencies**: Ensure all packages are installed
4. **Check Port Conflicts**: Make sure ports 8000, 5050, 5001 are available

### Log Rotation Not Working

If logs aren't rotating:

1. **Check Permissions**: Ensure write access to `logs/` directory
2. **Verify Monitoring**: Monitoring thread must be running
3. **Check Log Size**: Rotation only happens when size > 10MB

## Advanced Configuration

### Customizing Log Rotation

Edit `run_platform.py` to change rotation settings:

```python
# In PlatformLauncher.__init__()
self.max_log_size = 20 * 1024 * 1024  # 20MB instead of 10MB
self.log_backup_count = 10  # Keep 10 backups instead of 5
```

### Customizing Monitoring Interval

Change the monitoring check frequency:

```python
# In monitor_services() method
time.sleep(10)  # Check every 10 seconds instead of 5
```

### Customizing Dashboard Refresh

Change the auto-refresh interval:

```python
# In interactive_dashboard() method
if select.select([sys.stdin], [], [], 10)[0]:  # 10 seconds instead of 5
```

## Performance Impact

### Resource Usage

- **CPU**: < 1% (background monitoring thread)
- **Memory**: ~5-10MB (dashboard + monitoring)
- **Disk I/O**: Minimal (only during log rotation)

### Recommendations

- Dashboard is lightweight and suitable for production use
- Monitoring thread has negligible performance impact
- Log rotation prevents disk space issues

## Integration with Other Tools

### Viewing Logs in Real-Time

While dashboard is running, you can still use traditional log viewing:

```bash
# In another terminal
tail -f logs/api_server.log
tail -f logs/oauth_server.log
tail -f logs/nicegui_server.log
```

### Combining with Health Checks

Run health checks while services are running:

```bash
# In another terminal
python3.11 run_platform.py --check
```

## Future Enhancements

Planned features for future releases:

- [ ] CPU and memory usage per service (requires `psutil`)
- [ ] Network traffic monitoring
- [ ] Custom alert thresholds
- [ ] Email/Slack notifications on crashes
- [ ] Historical uptime graphs
- [ ] Export monitoring data to CSV/JSON
- [ ] Web-based dashboard (in addition to terminal)

## Support

For issues or questions about the monitoring dashboard:

1. Check service logs in `logs/` directory
2. Run health check: `python3.11 run_platform.py --check`
3. Review this documentation
4. Check GitHub issues for known problems

---

**Last Updated**: 2026-02-03  
**Version**: 1.0.0  
**Compatibility**: Python 3.11+, macOS/Linux

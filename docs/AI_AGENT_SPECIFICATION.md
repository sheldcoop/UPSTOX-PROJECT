# AI Agent Workflow Specification

**Last Updated:** February 3, 2026  
**Purpose:** Guide for AI agents and developers working on this project

---

## 🎯 Overview

This document provides a comprehensive specification for AI agents (and human developers) working on the UPSTOX Trading Platform. It defines workflows, responsibilities, inputs/outputs, dependencies, and operational checks.

---

## 🤖 Agent Roles & Responsibilities

### Primary Agent: Trading Platform Engineer

**Capabilities Required:**
- Python backend development (Flask, SQLite/PostgreSQL)
- Frontend development (NiceGUI framework)
- Database schema design and optimization
- API integration (REST, WebSocket)
- Background job scheduling
- DevOps (Docker, systemd, nginx)

**Key Responsibilities:**
1. Maintain and extend 11 backend services
2. Build frontend pages (31 total, 12 complete)
3. Manage database schema (78+ tables)
4. Integrate Upstox API v2/v3
5. Schedule and monitor background jobs
6. Write tests and documentation
7. Deploy to production

---

## 📚 Required Knowledge Base

### Must Read Before Starting

1. **[HOME.md](../HOME.md)** - Complete project overview
2. **[README.md](../README.md)** - Quick start guide
3. **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Development setup
4. **[DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)** - Database schema
5. **[SHELL_SCRIPTS.md](SHELL_SCRIPTS.md)** - Automation scripts
6. **[BACKGROUND_JOBS.md](BACKGROUND_JOBS.md)** - Scheduler & jobs
7. **[docs/Upstox.md](Upstox.md)** - Upstox API reference

### Additional Resources

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
- **[TESTING.md](TESTING.md)** - Testing guidelines
- **[.github/debugging-protocol.md](../.github/debugging-protocol.md)** - Debugging guide
- **[.github/copilot-instructions.md](../.github/copilot-instructions.md)** - Project-specific patterns

---

## 🔄 Core Workflows

### Workflow 1: Adding a New Backend Feature

**Input:** Feature requirement (e.g., "Add support for bracket orders")

**Steps:**
1. **Research** - Check Upstox API documentation
2. **Design** - Plan database schema changes
3. **Implement Backend:**
   - Create/update script in `scripts/`
   - Add database tables (if needed)
   - Implement error handling and logging
4. **Create API Endpoint:**
   - Add route in `scripts/blueprints/`
   - Add to `scripts/api_server.py`
5. **Test:**
   - Write unit tests in `tests/`
   - Test manually with curl/Postman
6. **Document:**
   - Update API documentation
   - Add to feature list

**Output:** Working feature with tests and documentation

**Dependencies:**
- Database: `market_data.db`
- API: Upstox credentials in `.env`
- Tools: Python 3.11+, pytest

**Validation Checklist:**
- [ ] Code follows Black formatting
- [ ] No Flake8 errors
- [ ] Tests pass (`pytest tests/`)
- [ ] API returns expected response
- [ ] Database schema validated
- [ ] Documentation updated

---

### Workflow 2: Creating a New Frontend Page

**Input:** Page requirement (e.g., "Create alerts management page")

**Steps:**
1. **Identify Backend APIs:**
   - Find relevant endpoints in `scripts/blueprints/`
   - Test endpoints with curl
2. **Create Page File:**
   - Create `dashboard_ui/pages/new_page.py`
   - Import NiceGUI components
3. **Design Layout:**
   - Use NiceGUI ui.card, ui.table, ui.button
   - Follow existing page patterns
4. **Connect to Backend:**
   - Use `ui.run_javascript()` or Python HTTP client
   - Handle errors gracefully
5. **Add to Navigation:**
   - Update `sidebar.py` or `nicegui_dashboard.py`
6. **Test:**
   - Start services with `./start_nicegui.sh`
   - Test all interactions
   - Check responsiveness

**Output:** New frontend page integrated with backend

**Dependencies:**
- Backend: API server running on port 9000
- Frontend: NiceGUI running on port 8080
- Browser: Chrome/Firefox

**Validation Checklist:**
- [ ] Page loads without errors
- [ ] API calls work
- [ ] Error handling functional
- [ ] UI is responsive
- [ ] Navigation updated
- [ ] Screenshots taken

---

### Workflow 3: Managing NSE Scraping

**Input:** Need to fetch NSE index data

**Steps:**
1. **Understand Script:**
   - Review `scripts/update_nse_indices.py`
   - Check NSE_INDICES dictionary
2. **Test Manually:**
   ```bash
   python scripts/update_nse_indices.py
   ```
3. **Verify Data:**
   ```sql
   SELECT COUNT(*) FROM nse_index_membership;
   SELECT * FROM nse_index_membership WHERE index_name='NIFTY50';
   ```
4. **Schedule (if not already):**
   - Add to APScheduler (see BACKGROUND_JOBS.md)
   - Or add cron job
5. **Monitor:**
   - Check logs for errors
   - Verify data freshness

**Output:** NSE data updated in database

**Dependencies:**
- Internet connection
- NSE website accessibility
- Database: `market_data.db`

**Validation Checklist:**
- [ ] Script runs without errors
- [ ] Tables updated (nse_index_membership, nse_sector_info)
- [ ] Row counts match expected (NIFTY50 = 50 stocks)
- [ ] Timestamps are current
- [ ] Scheduled job configured

---

### Workflow 4: Handling Background Jobs

**Input:** Need to automate a recurring task

**Steps:**
1. **Define Job:**
   - Name, frequency, dependencies
   - What it does, expected duration
2. **Create Job Function:**
   - Add to `scripts/scheduler_service.py`
   - Include error handling
   - Add logging
3. **Configure Schedule:**
   ```python
   scheduler.add_job(
       func=my_job_function,
       trigger='cron',
       hour=23,
       minute=30,
       id='my_job',
       name='My Job Description'
   )
   ```
4. **Test Manually:**
   ```python
   from scripts.scheduler_service import my_job_function
   my_job_function()  # Test directly
   ```
5. **Deploy:**
   - Restart scheduler service
   - Monitor first execution
6. **Monitor:**
   - Check `sync_jobs` table
   - Check `sync_history` table
   - Review logs

**Output:** Automated background job running on schedule

**Dependencies:**
- APScheduler installed
- Scheduler service running
- Database access

**Validation Checklist:**
- [ ] Job function works standalone
- [ ] Job added to scheduler
- [ ] Schedule is correct (cron syntax)
- [ ] Job executes successfully
- [ ] Errors are logged
- [ ] Email notifications work (if configured)

---

### Workflow 5: Exporting Data to CSV/Excel

**Input:** Need to export data from database

**Steps:**
1. **Query Data:**
   ```python
   import pandas as pd
   import sqlite3
   
   conn = sqlite3.connect('market_data.db')
   df = pd.read_sql_query("SELECT * FROM candles_new WHERE symbol='NIFTY'", conn)
   ```
2. **Export CSV:**
   ```python
   df.to_csv('downloads/nifty_candles.csv', index=False)
   ```
3. **Export Excel:**
   ```python
   with pd.ExcelWriter('downloads/nifty_candles.xlsx', engine='openpyxl') as writer:
       df.to_excel(writer, sheet_name='NIFTY Candles', index=False)
   ```
4. **Create API Endpoint:**
   ```python
   @app.route('/api/export/candles/<symbol>')
   def export_candles(symbol):
       # ... query data
       # ... export to file
       return send_file(filepath, as_attachment=True)
   ```
5. **Add UI Button:**
   ```python
   ui.button('Download CSV', on_click=lambda: download_csv())
   ```

**Output:** Downloadable CSV/Excel files

**Dependencies:**
- pandas, openpyxl
- Database access
- Disk space

**Validation Checklist:**
- [ ] Data exports without errors
- [ ] File format is correct
- [ ] Data is complete (no truncation)
- [ ] File is downloadable from UI
- [ ] Large files handled (pagination/streaming)

---

### Workflow 6: Sending Email Notifications

**Input:** Need to send email alerts

**Steps:**
1. **Configure SMTP (in .env):**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_FROM=alerts@example.com
   EMAIL_TO=user@example.com
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_USE_TLS=true
   ```
2. **Create Email Function:**
   ```python
   import smtplib
   from email.mime.text import MIMEText
   from email.mime.multipart import MIMEMultipart
   
   def send_alert_email(subject, body):
       msg = MIMEMultipart()
       msg['From'] = os.getenv('EMAIL_FROM')
       msg['To'] = os.getenv('EMAIL_TO')
       msg['Subject'] = subject
       msg.attach(MIMEText(body, 'plain'))
       
       with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
           server.starttls()
           server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
           server.send_message(msg)
   ```
3. **Test Email:**
   ```python
   send_alert_email('Test Alert', 'This is a test email')
   ```
4. **Integrate with Alert System:**
   - Add to `scripts/alert_system.py`
   - Call on alert trigger
5. **Add Error Handling:**
   - Catch SMTP errors
   - Log failures
   - Retry with backoff

**Output:** Email notifications sent on events

**Dependencies:**
- SMTP server credentials
- Internet connection
- Email configuration in `.env`

**Validation Checklist:**
- [ ] Test email received
- [ ] Email formatting correct
- [ ] Errors are caught and logged
- [ ] Rate limiting implemented (don't spam)
- [ ] Works with Gmail/Outlook/custom SMTP

---

### Workflow 7: Database Schema Changes

**Input:** Need to add/modify database tables

**⚠️ CRITICAL WORKFLOW - Follow Carefully**

**Steps:**
1. **Backup Database:**
   ```bash
   ./scripts/backup_db.sh
   ```
2. **Design Schema Change:**
   - Document new tables/columns
   - Consider indexes
   - Plan migration path
3. **Create Migration Script:**
   ```python
   def migrate_v3_to_v4():
       conn = sqlite3.connect('market_data.db')
       cursor = conn.cursor()
       
       # Add new table
       cursor.execute("""
           CREATE TABLE IF NOT EXISTS new_table (
               id INTEGER PRIMARY KEY,
               data TEXT
           )
       """)
       
       # Add column to existing table
       cursor.execute("""
           ALTER TABLE existing_table
           ADD COLUMN new_column TEXT
       """)
       
       conn.commit()
       conn.close()
   ```
4. **Test Migration (on backup):**
   ```bash
   cp market_data.db market_data_test.db
   python migration_script.py  # Test on copy
   ```
5. **Validate Data:**
   ```python
   from scripts.database_validator import DatabaseValidator
   validator = DatabaseValidator()
   validator.validate_all()
   ```
6. **Run All Tests:**
   ```bash
   pytest tests/ -v
   ```
7. **Apply to Production (if tests pass):**
   ```bash
   python migration_script.py
   ```
8. **Update Documentation:**
   - Update DATABASE_ARCHITECTURE.md
   - Update schema diagrams

**Output:** Database schema updated without data loss

**Dependencies:**
- Database backup
- All tests passing
- Migration script tested

**Validation Checklist:**
- [ ] Backup created
- [ ] Migration tested on copy
- [ ] All tests pass
- [ ] Data validated
- [ ] No corruption detected
- [ ] Documentation updated
- [ ] Rollback plan documented

---

### Workflow 8: Debugging Issues

**Input:** Bug report or unexpected behavior

**Steps:**
1. **Review Debugging Protocol:**
   - Read `.github/debugging-protocol.md`
   - Follow God-Mode Debugging Protocol
2. **Triage:**
   - Generate 3-5 ranked hypotheses
   - Assign probability scores
3. **Instrument:**
   - Add trace_id logging
   - Add state snapshots
4. **Isolate:**
   - Create minimal `repro_debug.py` script
   - Reproduce bug in isolation
5. **Fix:**
   - Implement fix with assertions
   - Add validation
6. **Verify:**
   - Test fix
   - Add to regression suite

**Output:** Bug fixed with test coverage

**Dependencies:**
- Access to logs
- Ability to reproduce
- Test infrastructure

**Validation Checklist:**
- [ ] Bug reproduced
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Test added to prevent regression
- [ ] Documentation updated (if needed)

---

## 🔐 Operational Constraints

### Security Rules

1. **Never commit secrets:**
   - Always use `.env` for credentials
   - Never hardcode API keys
   - Use environment variables

2. **Validate all inputs:**
   - Sanitize user inputs
   - Use parameterized SQL queries
   - Validate API responses

3. **Encrypt sensitive data:**
   - OAuth tokens encrypted (Fernet)
   - Encryption key in `.env`

### Code Quality Standards

1. **Formatting:**
   ```bash
   black .
   ```

2. **Linting:**
   ```bash
   flake8 scripts/ dashboard_ui/
   ```

3. **Type hints (preferred):**
   ```python
   def process_data(symbol: str, data: List[Dict]) -> pd.DataFrame:
       ...
   ```

4. **Logging:**
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Processing {symbol}")
   ```

### Testing Requirements

1. **Unit tests for new features:**
   ```python
   def test_new_feature():
       # Arrange
       expected = ...
       
       # Act
       result = new_feature()
       
       # Assert
       assert result == expected
   ```

2. **Integration tests for API endpoints:**
   ```python
   def test_api_endpoint(client):
       response = client.get('/api/endpoint')
       assert response.status_code == 200
   ```

3. **Coverage threshold:** Aim for 80%+

---

## 📊 Success Metrics

### Development Metrics

- **Code Quality:** 100% Black formatted, 0 Flake8 errors
- **Test Coverage:** 80%+ line coverage
- **Documentation:** Every feature documented
- **Security:** 0 vulnerabilities (CodeQL scan)

### Operational Metrics

- **Uptime:** 99.9% API availability
- **Data Freshness:** NSE data < 24 hours old
- **Job Success Rate:** 99%+ background jobs succeed
- **Response Time:** API responses < 500ms (p95)

---

## 🚀 Deployment Checklist

Before deploying to production:

- [ ] All tests pass (`pytest tests/`)
- [ ] Code formatted (`black .`)
- [ ] No linting errors (`flake8`)
- [ ] Security scan clean (CodeQL)
- [ ] Database backed up
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Health checks passing
- [ ] Logs reviewed (no errors)
- [ ] Rollback plan documented

---

## 📞 Support & Escalation

### For AI Agents

**When stuck:**
1. Review relevant documentation
2. Check existing code for patterns
3. Search codebase for similar implementations
4. Ask user for clarification

**When uncertain:**
1. Explain reasoning
2. Provide options with pros/cons
3. Ask for user decision

**Never:**
- Delete working code without backup
- Commit secrets or credentials
- Make breaking changes without tests
- Skip documentation updates

### For Human Developers

**Resources:**
- Documentation: See links above
- GitHub Issues: Report bugs
- Code Review: Required for all PRs

---

## 🎯 Common Tasks Quick Reference

### Start Development Environment
```bash
./setup.sh
./authenticate.sh
./start_nicegui.sh
```

### Run Tests
```bash
pytest tests/ -v
pytest tests/test_specific.py
```

### Check Database
```bash
sqlite3 market_data.db
.tables
SELECT COUNT(*) FROM candles_new;
```

### Check Logs
```bash
tail -f logs/*.log
```

### Backup Database
```bash
./scripts/backup_db.sh
```

### Deploy to Production
```bash
./start_production.sh
```

---

## 📈 Continuous Improvement

### Regular Tasks

**Daily:**
- Monitor background jobs
- Check error logs
- Review alert notifications

**Weekly:**
- Review test coverage
- Update documentation
- Clean up old data

**Monthly:**
- Database maintenance (VACUUM, ANALYZE)
- Security audit
- Performance optimization
- Documentation review

---

**Agent Specification Version:** 1.0  
**Last Updated:** February 3, 2026  
**Maintained By:** Development Team

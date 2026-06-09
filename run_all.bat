@echo off
cd /d "%~dp0"

echo ========================================
echo  ETL Data Warehouse - Run All
echo ========================================
echo.

call conda activate .\.conda

echo [1/5] Initialize database...
python init_database.py
echo.

echo [2/5] Generate test data...
python generate_data.py
echo.

echo [3/5] Run ETL job...
python etl_job.py
echo.

echo [4/5] Run OLAP queries...
python olap_queries.py
echo.

echo [5/5] Generate charts...
python olap_charts.py
echo.

echo ========================================
echo  All tasks completed!
echo ========================================
pause

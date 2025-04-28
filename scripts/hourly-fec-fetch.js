// Hourly FEC Data Fetcher
// This script runs the FEC data fetcher on an hourly schedule
// Usage: node hourly-fec-fetch.js --duration=168 (runs for 7 days)
// Recovery mode: node hourly-fec-fetch.js --recover (fixes missing data)

const { fetchAndStoreFecData } = require('./fetch-fec-data');
const { setTimeout } = require('timers/promises');
const fs = require('fs');
const path = require('path');

// Path to progress file
const CACHE_DIR = path.resolve(__dirname, '../cache/fec');
const PROGRESS_FILE = path.resolve(CACHE_DIR, 'progress.json');

// Parse command line arguments
const args = process.argv.slice(2);
let duration = 168; // Default to 168 hours (7 days)
let interval = 60; // Default to 60 minutes
let generateReport = false;
let recoveryMode = false;

// Parse command line arguments
args.forEach(arg => {
  if (arg.startsWith('--duration=')) {
    const value = parseInt(arg.split('=')[1], 10);
    if (!isNaN(value) && value > 0) {
      duration = value;
    }
  }
  if (arg.startsWith('--interval=')) {
    const value = parseInt(arg.split('=')[1], 10);
    if (!isNaN(value) && value > 0) {
      interval = value;
    }
  }
  if (arg === '--report') {
    generateReport = true;
  }
  if (arg === '--recover') {
    recoveryMode = true;
  }
});

// Check if running as main script
if (require.main === module) {
  if (generateReport) {
    generateProgressReport();
  } else {
    runHourlyFetcher(duration, interval, recoveryMode).catch(err => {
      console.error('Error in hourly fetcher:', err);
      process.exit(1);
    });
  }
}

// Generate a detailed progress report
function generateProgressReport() {
  if (!fs.existsSync(PROGRESS_FILE)) {
    console.log('No progress file found. Run the fetcher first.');
    return;
  }
  
  try {
    const progress = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
    
    console.log('\n=== FEC DATA ACQUISITION PROGRESS REPORT ===\n');
    
    // Basic stats
    const totalProcessed = Object.keys(progress.processedPoliticians || {}).length;
    const withData = Object.values(progress.processedPoliticians || {})
      .filter(p => p.dataInDb).length;
    const withoutData = totalProcessed - withData;
    
    console.log(`Last run: ${progress.lastRunTimestamp || 'Never'}`);
    console.log(`Total politicians processed: ${totalProcessed}`);
    console.log(`Politicians with data: ${withData}`);
    console.log(`Politicians without data: ${withoutData}`);
    
    // Run history
    if (progress.runs && progress.runs.length > 0) {
      console.log('\n--- Run History ---');
      progress.runs.forEach((run, i) => {
        const startTime = new Date(run.startTime);
        const endTime = run.endTime ? new Date(run.endTime) : null;
        const duration = endTime ? ((endTime - startTime) / 1000 / 60).toFixed(1) : 'N/A';
        
        console.log(`Run #${i+1}: ${startTime.toLocaleString()}`);
        console.log(`  Duration: ${duration} minutes`);
        console.log(`  API calls: ${run.apiCalls}`);
        console.log(`  Politicians processed: ${run.politiciansProcessed}`);
      });
    }
    
    // Election year coverage
    const electionYears = new Set();
    const electionYearCounts = {};
    
    Object.values(progress.processedPoliticians || {}).forEach(p => {
      if (p.processedElectionYears && p.processedElectionYears.length > 0) {
        p.processedElectionYears.forEach(year => {
          electionYears.add(year);
          electionYearCounts[year] = (electionYearCounts[year] || 0) + 1;
        });
      }
    });
    
    if (electionYears.size > 0) {
      console.log('\n--- Election Year Coverage ---');
      const sortedYears = Array.from(electionYears).sort((a, b) => b - a);
      sortedYears.forEach(year => {
        console.log(`  ${year}: ${electionYearCounts[year]} politicians`);
      });
    }
    
    // Status breakdown
    const statusCounts = {};
    Object.values(progress.processedPoliticians || {}).forEach(p => {
      statusCounts[p.status] = (statusCounts[p.status] || 0) + 1;
    });
    
    if (Object.keys(statusCounts).length > 0) {
      console.log('\n--- Processing Status ---');
      Object.entries(statusCounts).forEach(([status, count]) => {
        console.log(`  ${status}: ${count} politicians`);
      });
    }
    
    console.log('\n=== END OF REPORT ===\n');
    
  } catch (error) {
    console.error('Error generating report:', error);
  }
}

// Function to run the fetcher on a schedule
async function runHourlyFetcher(hours = 168, intervalMinutes = 60, recover = false) {
  const startTime = new Date();
  const endTime = new Date(startTime.getTime() + (hours * 60 * 60 * 1000));
  
  console.log(`Starting hourly FEC data fetcher at ${startTime.toISOString()}`);
  console.log(`Will run for ${hours} hours (until ${endTime.toISOString()})`);
  console.log(`Interval between runs: ${intervalMinutes} minutes`);
  
  if (recover) {
    console.log('RECOVERY MODE ACTIVE: Will prioritize fixing missing data');
  }
  
  let runCount = 0;
  
  // Run immediately the first time
  try {
    runCount++;
    console.log(`\n=== Run #${runCount} at ${new Date().toISOString()} ===`);
    await fetchAndStoreFecData(recover);
    
    // Generate a report after each run
    generateProgressReport();
  } catch (error) {
    console.error(`Error during run #${runCount}:`, error);
  }
  
  // Then schedule subsequent runs
  while (new Date() < endTime) {
    // Calculate time until next run (in milliseconds)
    const waitTimeMs = intervalMinutes * 60 * 1000;
    const nextRunTime = new Date(Date.now() + waitTimeMs);
    
    console.log(`\nWaiting ${intervalMinutes} minutes until next run at ${nextRunTime.toLocaleString()}`);
    
    // Wait until next scheduled run
    await setTimeout(waitTimeMs);
    
    // Check if we've exceeded the end time
    if (new Date() >= endTime) {
      break;
    }
    
    // Run the fetcher
    try {
      runCount++;
      console.log(`\n=== Run #${runCount} at ${new Date().toISOString()} ===`);
      
      // Alternate between normal and recovery mode if in recovery mode
      const shouldRecover = recover && runCount % 2 === 0;
      if (recover) {
        console.log(`Run #${runCount} mode: ${shouldRecover ? 'RECOVERY' : 'NORMAL'}`);
      }
      
      await fetchAndStoreFecData(shouldRecover);
      
      // Generate a report after each run
      generateProgressReport();
    } catch (error) {
      console.error(`Error during run #${runCount}:`, error);
    }
  }
  
  console.log(`\nCompleted ${runCount} runs over ${hours} hours`);
  console.log(`Hourly FEC data fetcher finished at ${new Date().toISOString()}`);
  
  // Final report
  generateProgressReport();
}

module.exports = {
  runHourlyFetcher,
  generateProgressReport
}; 
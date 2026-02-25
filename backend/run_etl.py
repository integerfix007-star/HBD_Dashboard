import time
import subprocess
import sys
import os

def main():
    print("🔄 Starting ETL Background Runner...")
    
    # Ensure we are in the correct directory
    script_path = os.path.join(os.path.dirname(__file__), "etl_pipeline.py")
    
    while True:
        try:
            print(f"\n⏳ Running ETL Batch at {time.strftime('%X')}...")
            
            # Run the pipeline script
            # We use subprocess to isolate the execution context (memory, connections)
            result = subprocess.run([sys.executable, script_path], capture_output=False)
            
            if result.returncode != 0:
                print(f"⚠️ Pipeline exited with error code {result.returncode}.")
            
            # Optional: Dynamic sleep based on processing?
            # For high throughput, we sleep less.
            print("💤 Waiting 2 seconds before next batch...")
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n🛑 Runner stopped by user.")
            break
        except Exception as e:
            print(f"🔥 Runner infrastructure error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()

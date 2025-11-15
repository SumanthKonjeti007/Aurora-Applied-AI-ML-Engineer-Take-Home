(source venv/bin/activate && python3 << 'EOF'
      import json
      import pandas as pd

      # Load messages
      with open('data/raw_messages.json') as f:
          messages = json.load(f)

      print("="*60)
      print("DATA QUALITY ANALYSIS")
      print("="*60)

      df = pd.DataFrame(messages)

      print("\n1. BASIC INFO")
      print("-" * 60)
      print(f"Total messages: {len(df)}")
      print(f"Columns: {list(df.columns)}")
      print(f"\nData types:")
      print(df.dtypes)

      print("\n2. MISSING/NULL VALUES")
      print("-" * 60)
      print(df.isnull().sum())

      print("\n3. EMPTY OR WHITESPACE MESSAGES")
      print("-" * 60)
      empty = df[df['message'].str.strip() == '']
      print(f"Empty messages: {len(empty)}")

      print("\n4. DUPLICATE CHECK")
      print("-" * 60)
      print(f"Duplicate IDs: {df['id'].duplicated().sum()}")
      print(f"Duplicate message text: {df['message'].duplicated().sum()}")

      print("\n5. SAMPLE MESSAGES (First 10)")
      print("-" * 60)
      for i in range(min(10, len(messages))):
          msg = messages[i]
          print(f"\n{i+1}.")
          print(f"  User: {msg['user_name']}")
          print(f"  Message: {msg['message']}")
          print(f"  Length: {len(msg['message'])} chars")

      print("\n6. MESSAGE LENGTH STATS")
      print("-" * 60)
      df['length'] = df['message'].str.len()
      print(df['length'].describe())

      print("\n7. SPECIAL CHARACTER CHECKS")
      print("-" * 60)
      checks = {
          'Newlines': df['message'].str.contains(r'\n', regex=True).sum(),
          'Tabs': df['message'].str.contains(r'\t', regex=True).sum(),
          'Leading/trailing spaces': (df['message'] != df['message'].str.strip()).sum(),
          'Multiple consecutive spaces': df['message'].str.contains(r'  ', regex=True).sum(),
          'Non-ASCII characters': df['message'].str.contains(r'[^\x00-\x7F]', regex=True).sum(),
      }

      for check, count in checks.items():
          pct = (count/len(df))*100 if len(df) > 0 else 0
          print(f"{check}: {count} ({pct:.1f}%)")

      print("\n8. USER NAMES CHECK")
      print("-" * 60)
      print(f"Unique users: {df['user_name'].nunique()}")
      print("\nUser distribution:")
      print(df['user_name'].value_counts())

      print("\n9. TIMESTAMP ANALYSIS")
      print("-" * 60)
      df['ts'] = pd.to_datetime(df['timestamp'])
      print(f"Date range: {df['ts'].min()} to {df['ts'].max()}")
      print(f"All timestamps valid: {df['ts'].notna().all()}")

      print("\n10. POTENTIAL ISSUES TO ADDRESS")
      print("-" * 60)

      issues = []

      if df.isnull().any().any():
          issues.append("⚠️  Has NULL values")

      if len(empty) > 0:
          issues.append(f"⚠️  Has {len(empty)} empty messages")

      if df['message'].duplicated().sum() > 0:
          issues.append(f"⚠️  Has {df['message'].duplicated().sum()} duplicate messages")

      if (df['message'] != df['message'].str.strip()).sum() > 0:
          issues.append("⚠️  Has messages with leading/trailing whitespace")

      if df['message'].str.contains(r'  ', regex=True).sum() > 0:
          issues.append("⚠️  Has messages with multiple consecutive spaces")

      if len(issues) == 0:
          print("✅ No major data quality issues found!")
      else:
          print("Found issues:")
          for issue in issues:
              print(f"  {issue}")

      print("\n" + "="*60)
      print("RECOMMENDATION")
      print("="*60)

      if len(issues) == 0:
          print("✅ Data is clean. Minimal preprocessing needed.")
          print("   - Can use data as-is from API")
      else:
          print("⚠️  Preprocessing recommended:")
          print("   - Strip whitespace")
          print("   - Remove duplicates (if any)")
          print("   - Handle NULL values (if any)")

      EOF
      )
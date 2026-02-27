FIELD_DEFINITIONS = {
        # 1. Personal Information
        "Full Name": {"type": "text", "rule": "C", "required": True},
        "Gender": {"type": "text", "rule": "C", "required": False},
        "DOB": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},
        "SSN": {"type": "text", "rule": "C", "required": False},
        "Address 1": {"type": "text", "rule": "C", "required": False},
        "Address 2": {"type": "text", "rule": "C", "required": False},
        "City": {"type": "text", "rule": "C", "required": False},
        "State": {"type": "text", "rule": "C", "required": False},
        "Postal": {"type": "text", "rule": "C", "required": False},
        "Country": {"type": "text", "rule": "C", "required": False},
        "Email": {"type": "email", "rule": "D", "required": False},
        "Contact": {"type": "phone", "rule": "E", "required": False},

        # 2. Account Information
        "Customer ID": {"type": "number", "rule": "A", "required": True},
        "A/C Type": {"type": "text", "rule": "C", "required": False},
        "A/c Name": {"type": "text", "rule": "C", "required": False},
        "A/c Number": {"type": "text", "rule": "C", "required": False},
        "IBAN": {"type": "text", "rule": "C", "required": False}, # Add validation later
        "BIC": {"type": "text", "rule": "C", "required": False},
        "BTC Address": {"type": "text", "rule": "C", "required": False},
        "ETH Address": {"type": "text", "rule": "C", "required": False},
        "LTC Address": {"type": "text", "rule": "C", "required": False},
        "CC_No": {"type": "number", "rule": "A", "required": False},
        "Last Txn Amount": {"type": "currency", "rule": "B", "required": False},
        "Last Txn Date": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},

        # 3. Investment Information
        "Company": {"type": "text", "rule": "C", "required": False},
        "BS": {"type": "text", "rule": "C", "required": False},
        "EIN": {"type": "text", "rule": "C", "required": False},
        "Skill Description": {"type": "text", "rule": "C", "required": False},
        "ISIN": {"type": "text", "rule": "C", "required": False},
        "Coupon": {"type": "currency", "rule": "B", "required": False},
        "Invested Amount": {"type": "currency", "rule": "B", "required": False},
        "Maturity Date": {"type": "date", "rule": "F", "format": "%m/%d/%Y"},
        "Bond Name": {"type": "text", "rule": "C", "required": False},
        "Bond Class": {"type": "text", "rule": "C", "required": False},

        # 4. Assets & Last Purchase Information
        # 4.1 Last Purchase Detail
        "Department": {"type": "text", "rule": "C", "required": False},
        "Ean13": {"type": "text", "rule": "C", "required": False},
        "Product Name": {"type": "text", "rule": "C", "required": False},
        "Unit Price": {"type": "currency", "rule": "B", "required": False},
        "User": {"type": "text", "rule": "C", "required": False},
        "Purchase Token": {"type": "text", "rule": "C", "required": False},
        "Buying IPv4": {"type": "text", "rule": "C", "required": False},
        "Buying IPv6": {"type": "text", "rule": "C", "required": False},
        # 4.2 Vehicle Detail
        "Type": {"type": "text", "rule": "C", "required": False},
        "Model": {"type": "text", "rule": "C", "required": False},
        "Manufacture": {"type": "text", "rule": "C", "required": False},
        "VIN": {"type": "text", "rule": "C", "required": False},
        # 4.3 Insurance Detail
        "Beneficiary Identifier ID": {"type": "text", "rule": "C", "required": False},
        "INS No": {"type": "text", "rule": "C", "required": False},

        # 5. Legal Advisors
        # 5.1 Account Advisor
        "Account Advisor - Advisor ID": {"type": "text", "rule": "C", "required": False},
        "Account Advisor - Name": {"type": "text", "rule": "C", "required": False},
        "Account Advisor - Contact": {"type": "phone", "rule": "E", "required": False},
        "Account Advisor - Address": {"type": "text", "rule": "C", "required": False},
        # 5.2 Assets Manager
        "Assets Manager - Advisor ID": {"type": "text", "rule": "C", "required": False},
        "Assets Manager - Name": {"type": "text", "rule": "C", "required": False},
        "Assets Manager - Contact": {"type": "phone", "rule": "E", "required": False},
        "Assets Manager - Address": {"type": "text", "rule": "C", "required": False},
        # 5.3 Investment Advisor
        "Investment Advisor - Manager ID": {"type": "text", "rule": "C", "required": False},
        "Investment Advisor - Name": {"type": "text", "rule": "C", "required": False},
        "Investment Advisor - Contact": {"type": "phone", "rule": "E", "required": False},
        "Investment Advisor - Address": {"type": "text", "rule": "C", "required": False},
        # 5.4 Insurance Manager 
        "Insurance Manager - Manager ID": {"type": "text", "rule": "C", "required": False},
        "Insurance Manager - Name": {"type": "text", "rule": "C", "required": False},
        "Insurance Manager - Contact": {"type": "phone", "rule": "E", "required": False},
        "Insurance Manager - Address": {"type": "text", "rule": "C", "required": False},
    }

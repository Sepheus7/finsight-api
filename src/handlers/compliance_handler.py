"""
Compliance Handler for AWS Lambda
Checks for regulatory compliance issues in financial content
"""

import json
import os
import boto3
import re
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
COMPLIANCE_RULES_TABLE = os.environ.get('COMPLIANCE_RULES_TABLE')

def lambda_handler(event, context):
    """
    Lambda handler for compliance checking
    """
    try:
        content = event.get('content', '')
        request_id = event.get('request_id', context.aws_request_id)

        logger.info(f"Processing compliance check for request {request_id}")

        compliance_checker = ComplianceChecker()
        
        # Check for compliance issues
        compliance_flags = compliance_checker.check_compliance(content)
        
        # Get severity levels for flags
        flagged_issues = []
        for flag in compliance_flags:
            severity = compliance_checker.get_flag_severity(flag)
            flagged_issues.append({
                'flag': flag,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            })

        response_data = {
            'compliance_flags': compliance_flags,
            'flagged_issues': flagged_issues,
            'compliance_score': compliance_checker.calculate_compliance_score(flagged_issues),
            'request_id': request_id
        }

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }

    except Exception as e:
        logger.error(f"Compliance checking failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
            'error': str(e),
            'compliance_flags': [],
            'flagged_issues': [],
            'compliance_score': 0.0
            })
        }


class ComplianceChecker:
    def __init__(self):
        self.rules = self._load_compliance_rules()

    def check_compliance(self, text: str) -> List[str]:
        """Check for potential compliance issues"""
        flags = []
        
        # Investment advice without disclaimers
        if self._check_investment_advice_without_disclaimers(text):
            flags.append("Investment advice provided without proper disclaimers")
        
        # Guaranteed returns claims
        if self._check_guaranteed_returns(text):
            flags.append("Claims of guaranteed returns or profits")
        
        # Missing risk disclosures
        if self._check_missing_risk_disclosure(text):
            flags.append("Investment discussion without adequate risk disclosure")
        
        # Unauthorized financial advice
        if self._check_unauthorized_advice(text):
            flags.append("Potential unauthorized financial advisory services")
        
        # Market manipulation language
        if self._check_market_manipulation(text):
            flags.append("Language that could be construed as market manipulation")
        
        # Insider trading implications
        if self._check_insider_trading_language(text):
            flags.append("Content may imply use of material non-public information")
        
        # Misleading performance claims
        if self._check_misleading_performance(text):
            flags.append("Potentially misleading performance representations")
        
        # Suitability concerns
        if self._check_suitability_issues(text):
            flags.append("Investment recommendations without suitability assessment")
        
        # Anti-money laundering red flags
        if self._check_aml_concerns(text):
            flags.append("Content may raise anti-money laundering concerns")
        
        # Data privacy compliance
        if self._check_privacy_concerns(text):
            flags.append("Potential personal data privacy issues")

        return flags

    def _check_investment_advice_without_disclaimers(self, text: str) -> bool:
        """Check for investment advice without proper disclaimers"""
        advice_patterns = [
            r'(?:should|must|need to|ought to)\s+(?:buy|sell|invest|trade|purchase)',
            r'(?:I recommend|we recommend|my recommendation)\s+(?:buying|selling|investing)',
            r'(?:go long|go short|take a position)\s+(?:on|in)',
            r'(?:this is a|it\'s a)\s+(?:buy|sell|strong buy|strong sell)',
            r'(?:you should|you must)\s+(?:consider|look at|invest in)'
        ]
        
        disclaimer_patterns = [
            r'not financial advice',
            r'not investment advice',
            r'consult.*financial advisor',
            r'this is not a recommendation',
            r'for educational purposes',
            r'past performance.*not.*guarantee',
            r'investments.*risk'
        ]
        
        has_advice = any(re.search(pattern, text, re.IGNORECASE) for pattern in advice_patterns)
        has_disclaimer = any(re.search(pattern, text, re.IGNORECASE) for pattern in disclaimer_patterns)
        
        return has_advice and not has_disclaimer

    def _check_guaranteed_returns(self, text: str) -> bool:
        """Check for claims of guaranteed returns"""
        guarantee_patterns = [
            r'guaranteed.*(?:return|profit|gain)',
            r'(?:certain|sure|definite).*(?:return|profit)',
            r'(?:will|shall).*(?:definitely|certainly).*(?:increase|profit|return)',
            r'risk-free.*(?:return|investment|profit)',
            r'no risk.*(?:investment|return)',
            r'cannot lose',
            r'zero risk',
            r'guaranteed.*success'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in guarantee_patterns)

    def _check_missing_risk_disclosure(self, text: str) -> bool:
        """Check for investment discussion without risk disclosure"""
        investment_keywords = [
            'investment', 'portfolio', 'returns', 'profit', 'trading', 'stocks', 
            'bonds', 'options', 'futures', 'crypto', 'mutual fund', 'etf'
        ]
        
        risk_keywords = [
            'risk', 'loss', 'volatile', 'fluctuation', 'uncertainty', 'caution',
            'past performance', 'may lose', 'potential loss'
        ]
        
        has_investment_content = any(keyword in text.lower() for keyword in investment_keywords)
        has_risk_disclosure = any(keyword in text.lower() for keyword in risk_keywords)
        
        return has_investment_content and not has_risk_disclosure and len(text) > 100

    def _check_unauthorized_advice(self, text: str) -> bool:
        """Check for language suggesting unauthorized financial advisory services"""
        advisor_patterns = [
            r'as your (?:advisor|financial advisor)',
            r'I am (?:licensed|certified|qualified).*(?:advisor|planner)',
            r'my (?:financial planning|advisory) services',
            r'as a (?:registered|licensed).*(?:advisor|planner)',
            r'my (?:clients|portfolio management)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in advisor_patterns)

    def _check_market_manipulation(self, text: str) -> bool:
        """Check for language that could constitute market manipulation"""
        manipulation_patterns = [
            r'(?:pump|dump).*(?:stock|coin|price)',
            r'(?:buy now|everyone buy).*(?:before|to drive)',
            r'(?:spread the word|tell everyone).*(?:buy|invest)',
            r'(?:coordinated|group).*(?:buying|selling)',
            r'(?:artificial|fake).*(?:demand|supply)',
            r'(?:corner|squeeze).*market'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in manipulation_patterns)

    def _check_insider_trading_language(self, text: str) -> bool:
        """Check for content that might imply insider trading"""
        insider_patterns = [
            r'(?:inside|confidential|private).*information',
            r'(?:non-public|material).*information',
            r'(?:heard from|source at|friend at).*(?:company|firm)',
            r'(?:before.*announcement|before.*public)',
            r'(?:insider|internal).*(?:knowledge|tip)',
            r'(?:privileged|confidential).*(?:information|data)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in insider_patterns)

    def _check_misleading_performance(self, text: str) -> bool:
        """Check for potentially misleading performance claims"""
        misleading_patterns = [
            r'(?:\d+)%.*(?:returns?|gains?).*(?:guaranteed|always|every time)',
            r'(?:never lost|always profitable|100% success)',
            r'(?:beat the market|outperform).*(?:guaranteed|always)',
            r'(?:triple|double).*(?:your money|investment).*(?:guaranteed|certain)',
            r'(?:get rich|become wealthy).*(?:quick|fast|overnight)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in misleading_patterns)

    def _check_suitability_issues(self, text: str) -> bool:
        """Check for investment recommendations without suitability considerations"""
        recommendation_patterns = [
            r'(?:everyone should|all investors should|you should all)',
            r'(?:perfect for|ideal for).*(?:everyone|all investors)',
            r'(?:regardless of|no matter).*(?:age|income|risk tolerance)',
            r'(?:one size fits all|universal solution)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in recommendation_patterns)

    def _check_aml_concerns(self, text: str) -> bool:
        """Check for anti-money laundering red flags"""
        aml_patterns = [
            r'(?:cash only|no questions asked|anonymous)',
            r'(?:offshore|tax haven|hide.*money)',
            r'(?:launder|wash).*(?:money|funds)',
            r'(?:avoid.*taxes|tax evasion)',
            r'(?:under the table|off the books)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in aml_patterns)

    def _check_privacy_concerns(self, text: str) -> bool:
        """Check for potential privacy violations"""
        privacy_patterns = [
            r'(?:social security|ssn|social security number)',
            r'(?:bank account|routing number|account number)',
            r'(?:credit card|card number|cvv)',
            r'(?:personal information|private data).*(?:share|collect|store)',
            r'(?:without consent|unauthorized access)'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in privacy_patterns)

    def get_flag_severity(self, flag: str) -> str:
        """Get severity level for compliance flag"""
        high_severity_flags = [
            "Claims of guaranteed returns or profits",
            "Language that could be construed as market manipulation",
            "Content may imply use of material non-public information",
            "Potential unauthorized financial advisory services",
            "Content may raise anti-money laundering concerns"
        ]
        
        medium_severity_flags = [
            "Investment advice provided without proper disclaimers",
            "Potentially misleading performance representations",
            "Investment recommendations without suitability assessment"
        ]
        
        if flag in high_severity_flags:
            return "HIGH"
        elif flag in medium_severity_flags:
            return "MEDIUM"
        else:
            return "LOW"

    def calculate_compliance_score(self, flagged_issues: List[Dict]) -> float:
        """Calculate overall compliance score"""
        if not flagged_issues:
            return 1.0
        
        penalty_weights = {
            "HIGH": 0.3,
            "MEDIUM": 0.15,
            "LOW": 0.05
        }
        
        total_penalty = sum(penalty_weights.get(issue['severity'], 0.1) for issue in flagged_issues)
        compliance_score = max(0.0, 1.0 - total_penalty)
        
        return round(compliance_score, 2)

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules from DynamoDB (placeholder)"""
        # In production, this would load rules from DynamoDB
        # For now, return empty dict as rules are hardcoded in methods
        return {}

    def get_remediation_suggestions(self, flags: List[str]) -> List[str]:
        """Get suggestions for addressing compliance flags"""
        suggestions = []
        
        for flag in flags:
            if "disclaimers" in flag.lower():
                suggestions.append("Add appropriate disclaimers such as 'This is not financial advice' or 'Consult a qualified financial advisor'")
            
            elif "guaranteed" in flag.lower():
                suggestions.append("Remove language suggesting guaranteed returns and add risk disclosures")
            
            elif "risk disclosure" in flag.lower():
                suggestions.append("Include appropriate risk warnings such as 'Investments may lose value' or 'Past performance does not guarantee future results'")
            
            elif "unauthorized" in flag.lower():
                suggestions.append("Clarify that content is educational only and does not constitute professional financial advice")
            
            elif "manipulation" in flag.lower():
                suggestions.append("Remove language that could be construed as attempting to influence market prices")
            
            elif "insider" in flag.lower():
                suggestions.append("Ensure all information shared is publicly available and properly sourced")
            
            elif "misleading" in flag.lower():
                suggestions.append("Include context about market volatility and the possibility of losses")
            
            elif "suitability" in flag.lower():
                suggestions.append("Add language noting that investment suitability varies by individual circumstances")
        
        return suggestions

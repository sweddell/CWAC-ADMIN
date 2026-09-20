"""
Custom Example Audit Plugin for CWAC
This is a template for creating your own accessibility audit plugins.
"""

from typing import Any, Dict, List
from src.audits.base_audit import BaseAudit
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import logging

logger = logging.getLogger('cwac')


class CustomExampleAudit(BaseAudit):
    """
    Example custom audit that checks for specific accessibility patterns.
    
    This example checks for:
    - Presence of skip navigation links
    - Main landmark usage
    - Form label associations
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the custom audit."""
        super().__init__(config)
        self.audit_name = "custom_example_audit"
        
    def run(self, driver: WebDriver, page_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run the custom audit checks.
        
        Args:
            driver: Selenium WebDriver instance
            page_state: Dictionary containing page information
            
        Returns:
            List of audit results
        """
        results = []
        url = page_state.get('url', '')
        
        try:
            # Check 1: Look for skip navigation links
            skip_nav_result = self._check_skip_navigation(driver)
            if skip_nav_result:
                results.append({
                    'type': 'warning',
                    'check': 'skip-navigation',
                    'message': skip_nav_result,
                    'url': url,
                    'element': 'body'
                })
            
            # Check 2: Look for main landmark
            main_landmark_result = self._check_main_landmark(driver)
            if main_landmark_result:
                results.append({
                    'type': 'warning',
                    'check': 'main-landmark',
                    'message': main_landmark_result,
                    'url': url,
                    'element': 'body'
                })
            
            # Check 3: Check form labels
            form_label_results = self._check_form_labels(driver)
            for result in form_label_results:
                result['url'] = url
                results.append(result)
                
            logger.info(f"Custom audit found {len(results)} issues on {url}")
            
        except Exception as e:
            logger.error(f"Error running custom audit on {url}: {str(e)}")
            results.append({
                'type': 'error',
                'check': 'custom-audit-error',
                'message': f"Custom audit failed: {str(e)}",
                'url': url
            })
        
        return results
    
    def _check_skip_navigation(self, driver: WebDriver) -> str:
        """Check for skip navigation links."""
        try:
            # Look for common skip navigation patterns
            skip_patterns = [
                "//a[contains(@href, '#main')]",
                "//a[contains(@href, '#content')]",
                "//a[contains(text(), 'Skip to')]",
                "//a[contains(@class, 'skip')]"
            ]
            
            skip_link_found = False
            for pattern in skip_patterns:
                try:
                    elements = driver.find_elements(By.XPATH, pattern)
                    if elements:
                        skip_link_found = True
                        break
                except:
                    continue
            
            if not skip_link_found:
                return "No skip navigation link found. Consider adding a skip link for keyboard users."
            
        except Exception as e:
            logger.debug(f"Error checking skip navigation: {str(e)}")
            
        return ""
    
    def _check_main_landmark(self, driver: WebDriver) -> str:
        """Check for proper use of main landmark."""
        try:
            # Check for <main> element or role="main"
            main_elements = driver.find_elements(By.TAG_NAME, "main")
            main_role_elements = driver.find_elements(By.XPATH, "//*[@role='main']")
            
            total_mains = len(main_elements) + len(main_role_elements)
            
            if total_mains == 0:
                return "No main landmark found. Use <main> element or role='main' to identify main content."
            elif total_mains > 1:
                return f"Multiple main landmarks found ({total_mains}). There should be only one main landmark per page."
            
        except Exception as e:
            logger.debug(f"Error checking main landmark: {str(e)}")
            
        return ""
    
    def _check_form_labels(self, driver: WebDriver) -> List[Dict[str, Any]]:
        """Check form inputs for proper labeling."""
        results = []
        
        try:
            # Find all form inputs that need labels
            input_types_needing_labels = ['text', 'email', 'password', 'tel', 'number', 'search', 'url']
            
            for input_type in input_types_needing_labels:
                inputs = driver.find_elements(By.XPATH, f"//input[@type='{input_type}']")
                
                for input_element in inputs:
                    try:
                        input_id = input_element.get_attribute('id')
                        aria_label = input_element.get_attribute('aria-label')
                        aria_labelledby = input_element.get_attribute('aria-labelledby')
                        placeholder = input_element.get_attribute('placeholder')
                        
                        # Check if input has proper labeling
                        has_label = False
                        
                        # Check for associated label element
                        if input_id:
                            labels = driver.find_elements(By.XPATH, f"//label[@for='{input_id}']")
                            if labels:
                                has_label = True
                        
                        # Check for aria-label or aria-labelledby
                        if aria_label or aria_labelledby:
                            has_label = True
                        
                        # Check if input is wrapped in label
                        parent = input_element.find_element(By.XPATH, "..")
                        if parent.tag_name.lower() == 'label':
                            has_label = True
                        
                        if not has_label:
                            # Only using placeholder is not sufficient
                            message = f"Input field (type='{input_type}') missing proper label"
                            if placeholder:
                                message += f" (only has placeholder: '{placeholder}')"
                            
                            results.append({
                                'type': 'error',
                                'check': 'form-label',
                                'message': message,
                                'element': f"input[type='{input_type}']"
                            })
                    
                    except Exception as e:
                        logger.debug(f"Error checking individual input: {str(e)}")
                        continue
            
            # Also check textareas and selects
            for tag in ['textarea', 'select']:
                elements = driver.find_elements(By.TAG_NAME, tag)
                for element in elements:
                    try:
                        elem_id = element.get_attribute('id')
                        aria_label = element.get_attribute('aria-label')
                        aria_labelledby = element.get_attribute('aria-labelledby')
                        
                        has_label = False
                        
                        if elem_id:
                            labels = driver.find_elements(By.XPATH, f"//label[@for='{elem_id}']")
                            if labels:
                                has_label = True
                        
                        if aria_label or aria_labelledby:
                            has_label = True
                        
                        parent = element.find_element(By.XPATH, "..")
                        if parent.tag_name.lower() == 'label':
                            has_label = True
                        
                        if not has_label:
                            results.append({
                                'type': 'error',
                                'check': 'form-label',
                                'message': f"{tag.capitalize()} element missing proper label",
                                'element': tag
                            })
                    
                    except Exception as e:
                        logger.debug(f"Error checking {tag}: {str(e)}")
                        continue
        
        except Exception as e:
            logger.error(f"Error checking form labels: {str(e)}")
        
        return results
    
    def get_result_filename(self) -> str:
        """Return the filename for saving results."""
        return "custom_example_audit_results.json"

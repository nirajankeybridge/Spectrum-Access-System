#    Copyright 2016 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import json
import os
import unittest
import sas
from util import winnforum_testcase
from datetime import datetime


class MeasurementTestcase(unittest.TestCase):

  def setUp(self):
    self._sas, self._sas_admin = sas.GetTestingSas()
    self._sas_admin.Reset()

  def tearDown(self):
    pass

  @winnforum_testcase
  def test_WINNF_FT_S_MES_1(self):
    """The sas under test to request measurement reporting
    Register cbsds 6 CBSDs with measCapability make sure the SAS request 
    The measurement report config.
    """

    # Load the devices
    device_a = json.load(
        open(os.path.join('testcases', 'testdata', 'device_a.json')))
    device_b = json.load(
        open(os.path.join('testcases', 'testdata', 'device_b.json')))
    device_c = json.load(
        open(os.path.join('testcases', 'testdata', 'device_c.json')))
    device_d = json.load(
        open(os.path.join('testcases', 'testdata', 'device_d.json')))
    device_e = json.load(
        open(os.path.join('testcases', 'testdata', 'device_e.json')))
    device_f = json.load(
        open(os.path.join('testcases', 'testdata', 'device_f.json')))
    devices = [device_a, device_b, device_c, device_d, device_e, device_f]

    for device in devices:
        # set meascapability for all devices to 'RECEIVED_POWER_WITHOUT_GRANT'
        device['measCapability'] = ['RECEIVED_POWER_WITHOUT_GRANT']
        # Inject FCC and user IDs
        self._sas_admin.InjectFccId({'fccId': device['fccId']})
        self._sas_admin.InjectUserId({'userId': device['userId']})

    # Trigger to request measurement report for spectrum Inquery and grant request
    self._sas_admin.TriggerMeasurementReportRegistration({'measReportConfig': []})
    cbsd_ids = []
    # Register devices
    request = {'registrationRequest': devices}
    response = self._sas.Registration(request)['registrationResponse']
    # Check registration response
    for resp in response:
        self.assertTrue('cbsdId' in resp)
        self.assertEqual(resp['measReportConfig'], 'RECEIVED_POWER_WITHOUT_GRANT')
        self.assertEqual(resp['response']['responseCode'], 0)
        cbsd_ids.append(resp['cbsdId'])

    del request, response
    # Create Spectrum Inquiry request  for the six devices
    spectrum_inquiries = []
    for cbsd_id in cbsd_ids:
        spectrum_inquiry = {}
        spectrum_inquiry['cbsdId'] = cbsd_id
        meas_report = json.load(
            open(os.path.join('testcases', 'testdata', 'meas_report_1.json')))
        spectrum_inquiry['measReport'] =  {'rcvdPowerMeasReports': meas_report}
        # Delete measRcvdPower for second devide
        if cbsd_id == cbsd_ids[1]:
            for meas_num, meas in enumerate(meas_report):
                del meas_report[meas_num]['measRcvdPower']
        # For the third device build array of 10 element for measReport
        if cbsd_id == cbsd_ids[2]:
            spectrum_inquiry['measReport'] =  {'rcvdPowerMeasReports': meas_report[:10]}
        # Delete rcvdPowerMeasReports for the 4th device
        if cbsd_id == cbsd_ids[3]:
            del spectrum_inquiry['measReport']['rcvdPowerMeasReports']
        # Delete MeasReport for the 5th device
        if cbsd_id == cbsd_ids[4]:
            del spectrum_inquiry['measReport']
        # For the 6th device set measBandwidth to 15000000 Hz
        if cbsd_id == cbsd_ids[5]:
            for meas_num, meas in enumerate(meas_report):
                meas_report[meas_num]['measBandwidth'] = 15000000
        spectrum_inquiry['inquiredSpectrum'] = [{
            'lowFrequency': 3550000000.0,
            'highFrequency': 3560000000.0
        }]
        spectrum_inquiries.append(spectrum_inquiry)
    # Send Spectrum Inquiry request
    request = {'spectrumInquiryRequest': spectrum_inquiries}
    response = self._sas.SpectrumInquiry(request)['spectrumInquiryResponse']
    # Check Spectrum Inquiry response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:5]:
        self.assertEqual(resp['response']['responseCode'], 102)
    self.assertEqual(response[5]['response']['responseCode'], 103)
    
    # Create Grant Request for the six devices
    grant_request = []
    for meas_num, meas_report in enumerate(spectrum_inquiries):
        grant_0 = json.load(
            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
        grant_0['operationParam']['operationFrequencyRange'][
            'lowFrequency'] = 3550000000.0
        grant_0['operationParam']['operationFrequencyRange'][
            'highFrequency'] = 3560000000.0
        grant_0['cbsdId'] = meas_report['cbsdId']
        if 'measReport' in meas_report:
            grant_0['measReport'] = meas_report['measReport']
        grant_request.append(grant_0)
    # Send Grant Request
    request = {'grantRequest': grant_request}
    response = self._sas.Grant(request)['grantResponse']
    # Check Spectrum Inquiry response
    self.assertEqual(response[0]['cbsdId'], cbsd_ids[0])
    self.assertTrue('grantId' in response[0])
    self.assertEqual(response[0]['response']['responseCode'], 0)
    for resp in response[1:5]:
        self.assertEqual(resp['response']['responseCode'], 102)
    self.assertEqual(response[5]['response']['responseCode'], 103)
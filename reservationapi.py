""" Reservation API wrapper

This class implements a simple wrapper around the reservation API. It
provides automatic retries for server-side errors, delays to prevent
server overloading, and produces sensible exceptions for the different
types of client-side error that can be encountered.
"""

# This file contains areas that need to be filled in with your own
# implementation code. They are marked with "Your code goes here".
# Comments are included to provide hints about what you should do.

import requests
try:
    import simplejson as json
except ImportError:
    import json
import warnings
import time

from requests.exceptions import HTTPError
from exceptions import (
    BadRequestError, InvalidTokenError, BadSlotError, NotProcessedError,
    SlotUnavailableError,ReservationLimitError)

class ReservationApi:
    def __init__(self, base_url: str, token: str, retries: int, delay: float):
        """ Create a new ReservationApi to communicate with a reservation
        server.

        Args:
            base_url: The URL of the reservation API to communicate with.
            token: The user's API token obtained from the control panel.
            retries: The maximum number of attempts to make for each request.
            delay: A delay to apply to each request to prevent server overload.
        """
        self.base_url = base_url
        self.token    = token
        self.retries  = retries
        self.delay    = delay

    def _reason(self, req: requests.Response) -> str:
        """Obtain the reason associated with a response"""
        reason = ''

        # Try to get the JSON content, if possible, as that may contain a
        # more useful message than the status line reason
        try:
            json = req.json()
            reason = json['message']

        # A problem occurred while parsing the body - possibly no message
        # in the body (which can happen if the API really does 500,
        # rather than generating a "fake" 500), so fall back on the HTTP
        # status line reason
        except simplejson.errors.JSONDecodeError:
            if isinstance(req.reason, bytes):
                try:
                    reason = req.reason.decode('utf-8')
                except UnicodeDecodeError:
                    reason = req.reason.decode('iso-8859-1')
            else:
                reason = req.reason

        return reason


    def _headers(self) -> dict:
        """Create the authorization token header needed for API requests"""
        # Your code goes here
        return {"Authorization": "Bearer " + self.token}


    def _send_request(self, method: str, endpoint: str) -> dict:
        """Send a request to the reservation API and convert errors to
           appropriate exceptions"""
        # Your code goes here
        url = self.base_url + endpoint

        for attempt in range (1 , self.retries + 1):
            try:
                response = requests. request(method, url, headers = self._headers())
            except Exception as e:
                warnings.warn(f"Request exception on try {attempt}/{self.retries}: {str(e)}")
                time.sleep(self.delay)
                continue

            time.sleep(self.delay)

            if response.status_code == 200:
                return response.json()

            elif 500 <= response.status_code < 600:
                warnings.warn(f"Server error (try {attempt}/{self.retries}): {response.status_code} - {self._reason(response)}")

            elif response.status_code == 400:
                raise BadRequestError(self._reason(response))
            elif response.status_code == 401:
                raise InvalidTokenError(self._reason(response))
            elif response.status_code == 403:
                raise BadSlotError(self._reason(response))
            elif response.status_code == 404:
                raise NotProcessedError(self._reason(response))
            elif response.status_code == 409:
                raise SlotUnavailableError(self._reason(response))
            elif response.status_code == 451:
                raise ReservationLimitError(self._reason(response))
            else:
                response.raise_for_status()

        raise Exception("Maximum retries exceeded, request failed.")

        # Allow for multiple retries if needed
            # Perform the request.

            # Delay before processing the response to avoid swamping server.

            # 200 response indicates all is well - send back the json data.

            # 5xx responses indicate a server-side error, show a warning
            # (including the try number).

            # 400 errors are client problems that are meaningful, so convert
            # them to separate exceptions that can be caught and handled by
            # the caller.

            # Anything else is unexpected and may need to kill the client.

        # Get here and retries have been exhausted, throw an appropriate
        # exception.


    def get_slots_available(self):
        """Obtain the list of slots currently available in the system"""
        # Your code goes here
        return self._send_request("GET", "/reservation/available")


    def get_slots_held(self):
        """Obtain the list of slots currently held by the client"""
        # Your code goes here
        return self._send_request("GET", "/reservation")


    def release_slot(self, slot_id):
        """Release a slot currently held by the client"""
        # Your code goes here
        endpoint = f"/reservation/{slot_id}"
        return self._send_request("DELETE", endpoint)

    def reserve_slot(self, slot_id):
        """Attempt to reserve a slot for the client"""
        # Your code goes here
        endpoint = f"/reservation/{slot_id}"
        return self._send_request("POST", endpoint)

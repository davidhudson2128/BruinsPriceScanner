import requests
import pprint
import email, smtplib, ssl
import time
import random

with open("stubhub_secrets.txt", "r") as secret_key_file:
    SECRET_STUBHUB_KEY, SENDER_EMAIL, SENDER_SMTP_PASSWORD, PHONE_NUMBER = secret_key_file.readlines()
    SECRET_STUBHUB_KEY = SECRET_STUBHUB_KEY.strip("\n")
    SENDER_EMAIL = SENDER_EMAIL.strip("\n")
    SENDER_SMTP_PASSWORD = SENDER_SMTP_PASSWORD.strip("\n")
    PHONE_NUMBER = PHONE_NUMBER.strip("\n")


def get_bruins_home_games():
    y = requests.get("https://api.stubhub.com/sellers/search/events/v3?performerId=2762&rows=500",
                     headers={"Authorization": f"Bearer {SECRET_STUBHUB_KEY}", "Accept": "application/json",
                              "Content-Type": "application/json", "Accept-Language": "en-US"})
    # print(y.headers)
    filtered_json = {}
    for event in y.json().get('events'):
        if event.get('venue').get('name') == 'TD Garden':
            for groupings in event.get('ancestors').get('groupings'):
                if groupings.get('id') == 108518:
                    filtered_json[len(filtered_json)] = event

    return filtered_json


def find_games_under_price_threshold(price_threshold, games_dict):
    games_under_price_threshold = []

    for i in range(len(games_dict)):
        game_name = games_dict[i].get('name')
        game_date_local = games_dict[i].get('eventDateLocal')
        min_price = games_dict[i].get('ticketInfo').get('minListPrice')

        # away_team =
        # print(f"Min ticket price for {game_name} on {game_date_local}: ${min_price}")
        # print(games_dict[i])

        if min_price <= price_threshold:
            games_under_price_threshold.append(games_dict[i])

    return games_under_price_threshold


def send_sms_via_email(number: str, message: str, subject: str, smtp_server: str = "smtp.gmail.com",
                       smtp_port: int = 465, sender_credentials: tuple = (SENDER_EMAIL, SENDER_SMTP_PASSWORD)):
    sender_email, email_password = sender_credentials
    receiver_email = f"{number}@{'tmomail.net'}"

    email_message = f"Subject:{subject}\nTo:{receiver_email}\n{message}"

    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=ssl.create_default_context()) as email:
        email.login(sender_email, email_password)
        for i in range(1):
            email.sendmail(sender_email, receiver_email, email_message)


def text_alert(game_info):
    subject = "Cheap Bruins game alert!"
    message = f"\n{game_info.get('name')} at ${game_info.get('ticketInfo').get('minListPrice')}"
    send_sms_via_email(number=PHONE_NUMBER, message=message, subject=subject)
    time.sleep(3)


if __name__ == '__main__':

    PRICE_THRESHOLD = 30
    interval_between_price_checks = 60 * 3
    time_between_texts = 60 * 30

    most_recent_text_time = time.time() - time_between_texts
    most_recent_still_working_text = time.time()

    while True:

        bruins_home_games_dict = get_bruins_home_games()
        list_of_games_under_price_threshold = find_games_under_price_threshold(PRICE_THRESHOLD, bruins_home_games_dict)
        for game in list_of_games_under_price_threshold:
            if time.time() - most_recent_text_time >= time_between_texts:
                text_alert(game)
                most_recent_text_time = time.time()

        # Still Working Texts
        if time.time() - most_recent_still_working_text >= 10 * 24 * 60 * 60:
            send_sms_via_email(number=PHONE_NUMBER, message='Scanner Running', subject='Bruins Ticket Scanner')
            most_recent_still_working_text = time.time()

        time.sleep(interval_between_price_checks)

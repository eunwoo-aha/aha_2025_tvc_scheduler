#!/usr/bin/env python3
import os
import pandas as pd
import json
import datetime
import pytz
from pathlib import Path
import calendar

# CSV 파일 경로
CSV_PATH = Path("data/aha_tvc_202505-202506.csv")

KOR_WEEKDAYS = ['월', '화', '수', '목', '금', '토', '일']

def format_time(time_str):
    """시간 문자열을 datetime 객체로 변환"""
    # 가정: 시간 형식이 'HH:MM' 형태
    hours, minutes = map(int, time_str.split(':'))
    return hours, minutes

def get_current_kst_datetime():
    """현재 한국 시간을 반환"""
    kst = pytz.timezone('Asia/Seoul')
    return datetime.datetime.now(kst)

def format_korean_datetime(date_str, day_of_week):
    # date_str: 'YYYY-MM-DD', day_of_week: '월', '화', ...
    year, month, day = date_str.split('-')
    return f"{year}년 {int(month):02d}월 {int(day):02d}일 ({day_of_week}요일)"

def format_korean_time(time_str):
    hour, minute = map(int, time_str.split(':'))
    if hour == 0:
        period = '오전'
        hour_display = 12
    elif hour < 12:
        period = '오전'
        hour_display = hour
    elif hour == 12:
        period = '오후'
        hour_display = 12
    else:
        period = '오후'
        hour_display = hour - 12
    return f"{period} {hour_display}시 {minute:02d}분"

def get_ad_type_label(ad_type):
    if ad_type == '프로그램':
        return '방송 시작 전후 랜덤'
    elif ad_type == '중간광고':
        return '중간에 나오는 광고'
    else:
        return ad_type

def check_tv_schedule():
    """TV 스케줄을 확인하고 알림을 준비"""
    # CSV 파일 읽기
    df = pd.read_csv(CSV_PATH, encoding='utf-8')

    # 현재 한국 시간
    now = get_current_kst_datetime()
    current_date = now.strftime('%Y-%m-%d')  # 가정: CSV의 날짜 형식이 'YYYY-MM-DD'

    # 임시로 날짜 형식을 맞춰주기 (실제로는 CSV의 형식에 맞게 조정 필요)
    # 가정: CSV의 방송일 형식이 'YYYY-MM-DD' 또는 'YYYYMMDD'
    if len(df['broadcast_date'].iloc[0]) == 8:  # 'YYYYMMDD' 형식인 경우
        df['broadcast_date'] = pd.to_datetime(df['broadcast_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

    # 오늘 방송되는 프로그램만 필터링
    today_programs = df[df['broadcast_date'] == current_date]

    if today_programs.empty:
        print("::set-output name=has_upcoming_program::false")
        print("::set-output name=has_ending_program::false")
        return

    # 현재 시간 (분 단위로 변환)
    current_total_minute = now.hour * 60 + now.minute

    upcoming_programs = []
    ending_programs = []

    # 각 프로그램을 확인
    for _, row in today_programs.iterrows():
        start_hour, start_minute = format_time(row['start_time'])
        end_hour, end_minute = format_time(row['end_time'])

        # 날짜를 datetime 객체로 변환하여 요일 추출
        date_obj = datetime.datetime.strptime(row['broadcast_date'], '%Y-%m-%d')
        day_of_week = KOR_WEEKDAYS[date_obj.weekday()]

        # 시작 5분 전 시간 계산 (분 단위)
        start_notification_total_minute = (start_hour * 60 + start_minute) - 5
        if start_notification_total_minute < 0:
            start_notification_total_minute += 24 * 60

        # 종료 5분 전 시간 계산 (분 단위)
        end_notification_total_minute = (end_hour * 60 + end_minute) - 5
        if end_notification_total_minute < 0:
            end_notification_total_minute += 24 * 60

        # 현재 시간이 시작 5분 전 0~4분 뒤(5분 미만)인지 확인
        is_start_time = 0 <= (start_notification_total_minute - current_total_minute) < 5
        # 현재 시간이 종료 5분 전 0~4분 뒤(5분 미만)인지 확인
        is_end_time = 0 <= (end_notification_total_minute - current_total_minute) < 5

        # 알림 조건 분기
        if row['ad_type'] == '중간광고':
            if is_start_time:
                upcoming_programs.append({
                    "program": row['program'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "ad_type": row['ad_type'],
                    "frequency": row['frequency'],
                    "broadcast_date": row['broadcast_date'],
                    "day_of_week": day_of_week
                })
        elif row['ad_type'] == '프로그램':
            if is_start_time:
                upcoming_programs.append({
                    "program": row['program'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "ad_type": row['ad_type'],
                    "frequency": row['frequency'],
                    "broadcast_date": row['broadcast_date'],
                    "day_of_week": day_of_week
                })
            if is_end_time:
                ending_programs.append({
                    "program": row['program'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "ad_type": row['ad_type'],
                    "frequency": row['frequency'],
                    "broadcast_date": row['broadcast_date'],
                    "day_of_week": day_of_week
                })
        else:
            if is_start_time:
                upcoming_programs.append({
                    "program": row['program'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "ad_type": row['ad_type'],
                    "frequency": row['frequency'],
                    "broadcast_date": row['broadcast_date'],
                    "day_of_week": day_of_week
                })
            if is_end_time:
                ending_programs.append({
                    "program": row['program'],
                    "start_time": row['start_time'],
                    "end_time": row['end_time'],
                    "ad_type": row['ad_type'],
                    "frequency": row['frequency'],
                    "broadcast_date": row['broadcast_date'],
                    "day_of_week": day_of_week
                })

    # 결과 설정
    has_upcoming = len(upcoming_programs) > 0
    has_ending = len(ending_programs) > 0

    # 시작 프로그램 알림 페이로드 준비
    if has_upcoming:
        upcoming_payload = {
            "username": "만나면 좋은 친구",  # 슬랙봇 이름 설정
            "icon_url": "https://media.a-ha.io/common/devops/slack/bot/mbc_icon.webp",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎬 곧 시작될 TV 광고 알림 :jangdoyeon_heart:",
                        "emoji": True
                    }
                }
            ]
        }

        for program in upcoming_programs:
            program_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{program['program']}*\n"
                            f"📅 방송 날짜: {format_korean_datetime(program.get('broadcast_date', current_date), program.get('day_of_week', ''))}\n"
                            f"▶️ 시작 시간: {format_korean_time(program['start_time'])}\n"
                            f"⏱️ 종료 시간: {format_korean_time(program['end_time'])}\n"
                            f"📺 광고 유형: {get_ad_type_label(program['ad_type'])}\n"
                            f"🔄 노출 횟수: {program['frequency']}"
                }
            }
            upcoming_payload["blocks"].append(program_block)

            # 구분선 추가
            upcoming_payload["blocks"].append({"type": "divider"})

        # 마지막 구분선 제거
        if upcoming_payload["blocks"][-1]["type"] == "divider":
            upcoming_payload["blocks"].pop()

        # 시청 권유 메시지 추가
        upcoming_payload["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "여러분! 우리 광고가 곧 송출됩니다. 👀"
            }
        })

    # 종료 프로그램 알림 페이로드 준비
    if has_ending:
        ending_payload = {
            "username": "만나면 좋은 친구",  # 슬랙봇 이름 설정
            "icon_url": "https://media.a-ha.io/common/devops/slack/bot/mbc_icon.webp",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔚 곧 종료될 TV 광고 알림 :jangdoyeon_munsan:",
                        "emoji": True
                    }
                }
            ]
        }

        for program in ending_programs:
            program_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{program['program']}*\n"
                            f"📅 방송 날짜: {format_korean_datetime(program.get('broadcast_date', current_date), program.get('day_of_week', ''))}\n"
                            f"▶️ 시작 시간: {format_korean_time(program['start_time'])}\n"
                            f"⏱️ 종료 시간: {format_korean_time(program['end_time'])}\n"
                            f"📺 광고 유형: {get_ad_type_label(program['ad_type'])}\n"
                            f"🔄 노출 횟수: {program['frequency']}"
                }
            }
            ending_payload["blocks"].append(program_block)

            # 구분선 추가
            ending_payload["blocks"].append({"type": "divider"})

        # 마지막 구분선 제거
        if ending_payload["blocks"][-1]["type"] == "divider":
            ending_payload["blocks"].pop()

        # 종료 메시지 추가
        ending_payload["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "프로그램이 곧 종료됩니다. 우리 광고를 놓치지 마세요! 🎯"
            }
        })

    # GitHub Action 출력 설정
    print(f"::set-output name=has_upcoming_program::{str(has_upcoming).lower()}")
    print(f"::set-output name=has_ending_program::{str(has_ending).lower()}")

    if has_upcoming:
        escaped_payload = json.dumps(upcoming_payload).replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')
        print(f"::set-output name=upcoming_program_payload::{escaped_payload}")

    if has_ending:
        escaped_payload = json.dumps(ending_payload).replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')
        print(f"::set-output name=ending_program_payload::{escaped_payload}")

if __name__ == "__main__":
    check_tv_schedule()
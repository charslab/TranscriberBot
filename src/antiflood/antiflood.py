import config
import time
import logging

logger = logging.getLogger(__name__)

flood_ratio = 2             # messages/seconds
max_flood_ratio = 10
time_threshold_warning = 5  # ratio > flood_ratio for {time_threshold_warning} seconds
time_threshold_flood = 10   # ratio > flood_ratio for {time_threshold_flood} seconds
timeout = 4                 # flood ends after ratio < flood_ratio for {timeout} seconds

callback_flood_warning = None
callback_flood_started = None
callback_flood_ended = None

LEVEL_NORMAL = 0
LEVEL_WARNING = 1
LEVEL_FLOOD = 2
# chat_id -> (level, ratio, msg_num, duration, last_update)
stats = {}

def register_flood_warning_callback(callback):
  global callback_flood_warning
  callback_flood_warning = callback

def register_flood_started_callback(callback):
  global callback_flood_started
  callback_flood_started = callback

def register_flood_ended_callback(callback):
  global callback_flood_ended
  callback_flood_ended = callback

def init():
  global flood_ratio, max_flood_ratio, time_threshold_warning, time_threshold_flood, timeout
  flood_ratio = config.get_config_prop("app")["antiflood"]["flood_ratio"]
  max_flood_ratio = config.get_config_prop("app")["antiflood"]["max_flood_ratio"]
  time_threshold_warning = config.get_config_prop("app")["antiflood"]["time_threshold_warning"]
  time_threshold_flood = config.get_config_prop("app")["antiflood"]["time_threshold_flood"]
  timeout = config.get_config_prop("app")["antiflood"]["timeout"]

  logger.info("Ratio: %d", flood_ratio)
  logger.info("Max flood ratio: %d", max_flood_ratio)
  logger.info("Thr warning: %d", time_threshold_warning)
  logger.info("Thr flood: %d", time_threshold_flood)
  logger.info("Timeout: %d", timeout)

def on_chat_msg_received(chat_id):
  global flood_ratio, time_threshold_warning, time_threshold_flood, timeout
  global callback_flood_warning, callback_flood_started, callback_flood_ended

  curr_time = time.time()

  if chat_id not in stats:
    stats[chat_id] = [LEVEL_NORMAL, 1.0, 1, 0.0, curr_time]

  else:
    level, ratio, msg_num, duration, last_update = stats[chat_id]
    updated_duration = duration + curr_time - last_update
    msg_num += 1
    curr_ratio = msg_num / updated_duration

    if curr_ratio < flood_ratio and updated_duration > timeout:
      curr_ratio, updated_duration, msg_num = 0, 0, 0
      level = LEVEL_NORMAL
      if callback_flood_ended:
        callback_flood_ended(chat_id)

    elif updated_duration > 1 and curr_ratio > max_flood_ratio and level < LEVEL_FLOOD:
      level = LEVEL_FLOOD
      logger.warning("Flood ratio for chat %d is over the top", chat_id)
      if callback_flood_started:
        callback_flood_started(chat_id)

    elif curr_ratio > flood_ratio:
      if updated_duration >= time_threshold_flood and level < LEVEL_FLOOD:
        logger.warning("Flood detected for chat %d", chat_id)
        level = LEVEL_FLOOD
        if callback_flood_started:
          callback_flood_started(chat_id)

      elif updated_duration >= time_threshold_warning and level < LEVEL_WARNING:
        logger.info("Potential flood for chat %d", chat_id)
        level = LEVEL_WARNING
        if callback_flood_warning is not None:
          callback_flood_warning(chat_id)

    stats[chat_id] = (level, curr_ratio, msg_num, updated_duration, curr_time)

    logger.info("stats[{}]: {}".format(chat_id, stats[chat_id]))



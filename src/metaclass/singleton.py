class Singleton(type):
  _instances = {}

  def __call__(cls, *args, **kwargs):
    k = (cls, args)
    if k not in cls._instances:
      cls._instances[k] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[k]
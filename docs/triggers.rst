Available Triggers
==================

.. toctree::


HotKeyTrigger
-------------

.. autoclass:: voice_commander.triggers.HotkeyTrigger

   .. automethod:: __init__

JoystickButtonTrigger
---------------------

.. TIP::
   Use ``python -m voice_commander joy-button-info`` to get joystick index and button numbers

.. autoclass:: voice_commander.triggers.JoystickButtonTrigger

   .. automethod:: __init__

Note: if you want to trigger on a POV hat, use :py:class:`voice_commander.triggers.JoystickAxisTrigger` instead.


JoystickAxisTrigger
-------------------

.. TIP::
   Use ``python -m voice_commander joy-axis-info`` to get joystick index and axis information


.. autoclass:: voice_commander.triggers.JoystickAxisTrigger

   .. automethod:: __init__


VoiceTrigger
------------

.. autoclass:: voice_commander.triggers.VoiceTrigger

   .. automethod:: __init__

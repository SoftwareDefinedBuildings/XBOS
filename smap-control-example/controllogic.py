def cool_controller(current_temperature, setpoint, deadband):
    print current_temperature, setpoint, deadband
    if current_temperature > setpoint + deadband:
        print 'COOL'
        return 1
    else:
        print 'NO COOL'
        return 0


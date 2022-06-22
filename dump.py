def get_ypr(self, forward, up):
        pitch = math.asin(-forward[Y])
        cospitch = sqrt(1 - forward[Y]**2)

        if cospitch == 0 or abs(forward[Y] >= 1):
            if pitch > 0:
                yaw = 0
                roll = atan2(-up[Z], -up[X]) + pi
            else:
                yaw = 0
                roll = -atan2(up[Z], up[X]) + pi
        else:
            cosYaw = forward[X]/cospitch
            sinYaw = forward[Z]/cospitch
            yaw = atan2(sinYaw, cosYaw)

            cosRoll = up[Y]/cospitch
            sinRoll = None
            if (abs(cosYaw) < abs(sinYaw)):
                sinRoll = -(up[X] + forward[Y]*cosRoll*cosYaw) / sinYaw
            else:
                sinRoll = up[Z] + forward[Y]*cosRoll*sinYaw / cosYaw
            
            roll = atan2(sinRoll, cosRoll)
        
        # mrp = self.rotation.as_mrp()
        # mrp_mag = np.linalg.norm(mrp)
        # angle = 4*math.atan(mrp_mag)
        # axis = mrp/angle


        return yaw * RAD_TO_DEG, pitch * RAD_TO_DEG, roll * RAD_TO_DEG

def animate(startVal, endVal, startTime, endTime, time):
    duration = (endTime-startTime)
    t = (time-startTime)/duration
    t = math.cos((t-1)*math.pi)*0.5+0.5

    val_range = endVal - startVal
    return startVal + t * val_range






def classify_oil_values(self):
        """
            Divides data into new data structures needed for various graphs.
        
            Args:
                self (object): The Oil starvation view itself.
                
        """

        # Initalizes the variables needed to store calculated data.
        self.total_starvation_events = 0
        self.oil_upper_timed = []
        self.oil_lower_timed = []
        self.lat_g_low = []
        self.lon_g_low = []
        self.lat_g_normal = []
        self.lon_g_normal = []
        self.lat_g_high = []
        self.lon_g_high = []
        self.pressure_excess = []
        self.starvation_distrobution_percentages = []
        self.starvation_distrobution = { 
            0 : [], 10 : [], 20 : [], 30 : [], 40 : [], 50 : [],
            60 : [], 70 : [], 80 : [], 90 : [], 100 : [], 110 : []
        }
        self.starvation_distrobution_rpm = {
            0 : [], 1000 : [], 2000 : [], 3000 : [], 4000 : [], 5000 : [],
            6000 : [], 7000 : [], 8000 : [], 9000 : [], 10000 : [], 11000 : [],
            12000 : [], 13000 : [], 14000 : [], 15000 : []
        }
        self.starvation_distrobution_keys = list(self.starvation_distrobution)
        self.starvation_distrobution_rpm_keys = list(self.starvation_distrobution_rpm)


        # Finds the upper and lower limit of each data point and scales it.
        for i in range(len(self.time)):
            for j in range(len(self.oil_operating_RPM)):
                if self.rpm[i] >= self.oil_operating_RPM[j]:
                    rpm_index = j
                else:
                    break
            self.oil_upper_timed.append(self.oil_operating_upper[rpm_index] * 100)
            self.oil_lower_timed.append(self.oil_operating_lower[rpm_index] * 100)

        # Classifies each g-force data point acording to that moments pressure limits.
        for i in range(len(self.lat_g)):
        
            for j in range(len(self.oil_operating_RPM)):
                          
                if round(self.rpm[i],-3) <= self.oil_operating_RPM[j]:
        
                    if self.oil_pressure[i] < self.oil_operating_lower[j]:
                        self.lat_g_low.append(self.lat_g[i])
                        self.lon_g_low.append(self.long_g[i])
                    elif self.oil_pressure[i] > self.oil_operating_upper[j]:
                        self.lat_g_high.append(self.lat_g[i])
                        self.lon_g_high.append(self.long_g[i])
                    else:
                        self.lat_g_normal.append(self.lat_g[i])
                        self.lon_g_normal.append(self.long_g[i])
        
                    break

        # Calculates the averages for each pressure classification.
        self.low_percent = len(self.lat_g_low)/len(self.lat_g)*100
        self.normal_percent = len(self.lat_g_normal)/len(self.lat_g)*100
        self.high_percent = len(self.lat_g_high)/len(self.lat_g)*100

        # Calculates the excess oil pressure at each data point and records the starvation for distrobution graph.
        for i in range(len(self.time)):

            excess_current_scaled = (self.oil_p_scaled[i] - (self.oil_lower_timed[i] + self.oil_upper_timed[i]) / 2 )
            excess_current = excess_current_scaled / -100
            self.pressure_excess.append(excess_current_scaled)

            if  0 < excess_current < 110 :
                self.starvation_distrobution[round(excess_current, -1)].append(excess_current)
                self.starvation_distrobution_rpm[round(self.rpm[i], -3)].append(excess_current)
                self.total_starvation_events += 1
 
        
            
        self.avg_excess = (sum(self.pressure_excess) / len(self.pressure_excess) / 100 )
        
        
        for i in range (len(self.starvation_distrobution)):
        
            self.starvation_distrobution_percentages.append(len(self.starvation_distrobution[i*10])/self.total_starvation_events*100)
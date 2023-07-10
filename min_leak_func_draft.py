#%% ATTEMPTING TO MAKE THIS OPTIMIZED IDK PLS WORK

    def minimize_power(self,params,inst,f_LO,device):
    #def min_power(inst, params):
    
        """

        DESCRIPTION:
        function to be optimized for minimizing LO leakage

        INPUTS:
        --------- 
        inst (class):
        params (float, array): voltages used for voltage offsets
        
        
        OUTPUTS:
        
        """
        
        V1, V2 = params
        inst.set(f'/{device}/sigouts/0/offset', V1)
        inst.set(f'/{device}/sigouts/1/offset', V2)
        inst.sync()
        power = self.get_power(fc =f_LO, plot = False, config = False)
        return np.min(power)
        # return power
    
    def minimize_leak(self,inst,f_LO=1e9,mode='fine',mixer='qubit',threshold=-50,measON=False,plot=False):
        """

        DESCRIPTION:
            Optimizes mixer at given frequency

        INPUTS:
            sa (class): API class instance of spectrum analyzer.
            inst (class): The class instance of the instrument (HDAWG or UHFQA) that controls the I and Q channels of the mixer we want to optimize.
            mode(string): Coarse or fine tuning. In "coarse" tuning mode the parameter steps are large.
            mixer (string): The mixer we want to optimize. Options are "qubit","resonator",and "stark". Defaults to 'qubit'.
            f_LO (float): The local oscillator (LO) frequency of the mixer. Defaults to 3.875e9.
            f_IF (float): The intermediate (IF) frequency of the mixer. Defaults to 50e6.
            amp (float): Amplitude of ON Pulse.
            channels (list): The AWG channel used for I/Q in the experimental setup.
            measON (boolean): Whether or not to measure the ON power of the mixer.
            plot (boolean): Whether or not to plot the leakage as a function the parameters.
        """
        
        if inst == self.awg:
            device = 'dev8233'
        elif inst == self.qa:
            device = 'dev2528'
            atten = self.qb_pars['rr_atten']
        
        start = time.time()
   
        vStart = np.zeros(2)
        for i in range(len(vStart)):
            vStart[i] = inst.get(f'/{device}/sigouts/{i}/offset')[f'{device}']['sigouts'][f'{i}']['offset']['value']
            inst.sync()
        
        span = 30.1e-3 if mode == 'coarse' else 5e-3
        dV  = 3e-3 if mode == 'coarse' else 0.5e-3

        bounds = [(vStart[0] - span/2, vStart[0] + span/2), (vStart[1] - span/2, vStart[1] + span/2)]
        objective_function = self.min_power
     
        
        if mixer == 'rr':
            self.update_qb_value('rr_atten', 0)
        else:
            pass
            
        self.config_sa(fc=f_LO,threshold=threshold)
            
        result = minimize(objective_function,x0 = vStart, args = (inst, f_LO, device),bounds = bounds)
        

        opt_I , opt_Q  = result.x
        inst.set(f'/{device}/sigouts/0/offset',opt_I)
        inst.set(f'/{device}/sigouts/1/offset',opt_Q)
        if inst == self.awg:
            self.update_qb_valueb('qb_mixer_offsets', [opt_I,opt_Q])
        elif inst == self.qa:
            self.update_qb_value('rr_mixer_offsets', [opt_I,opt_Q])
        inst.sync()
        print(f'optimal I_offset = {round(opt_I*1e3,1)} mV, optimal Q_offset = {round(1e3*opt_Q,1)} mV')

        end = time.time()
        print('%s mixer Optimization took %.1f seconds'%(mixer,(end-start)))

        # get LO leakage for optimal DC values
        OFF_power = self.get_power(fc=f_LO,threshold=threshold,plot=False)

        
        if mixer == 'rr':
            self.update_qb_value('rr_atten', atten)
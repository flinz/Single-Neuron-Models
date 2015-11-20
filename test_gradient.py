import copy
import matplotlib.pylab as plt


execfile('main.py')

neuron = TwoLayerNeuron()

neuron.run()

model = TwoLayerModel()

model.add_data(neuron)

state = optim.State(model)

Nk = np.shape(neuron.synapses.ker)[0]
Tk = np.shape(neuron.synapses.ker)[1]

F = state.basisKer

Nb = np.shape(F)[0]

Ker = np.zeros((Nk,np.shape(F)[1]),dtype='float')

Ker[:,:Tk] = neuron.synapses.ker/neuron.delta_v

state.paramKer[:state.N*Nb] = fun.Ker2Param(Ker,F)

expfun = fun.exp_fun(neuron.ASP_time,neuron.dt,neuron.ASP_total)

expfun = np.atleast_2d(expfun)

basASP = state.basisASP

print "------------------------------------------"

state.paramKer[state.N*Nb:-1] = fun.Ker2Param(expfun,basASP)

state.paramKer[-1] = neuron.threshold/neuron.delta_v

dv = (state.bnds[1] - state.bnds[0])*0.001

v = np.arange(state.bnds[0],state.bnds[1],dv)

v = np.atleast_2d(fun.sigmoid(neuron.non_linearity[0],v))

print "-------------------------------------------"

para = fun.Ker2Param(v,state.basisNL)

state.paramNL = np.hstack((para,para))

state.update()


gradientk = copy.copy(state.gradient_ker)
paramk = copy.copy(state.paramKer)
l0 = copy.copy(state.likelihood)

res = []
res_l = []

for r in range(100):

	print r
	state.paramKer = (r/90.)*paramk
	state.update()	
	res = res + [state.likelihood]

	res_l = res_l + [l0 + np.dot(gradientk.transpose(),(state.paramKer-paramk))]

res = np.array(res)
res_l = np.array(res_l)
plt.plot(res - res_l)
plt.show()




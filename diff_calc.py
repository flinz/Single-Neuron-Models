import numpy as np
from scipy import signal
import copy
import matplotlib.pylab as plt

def convolve(spike_train,basis,state):
	"""Each spike train has to be convoluted with all the basis functions. spike_train is a list of lists of spike times. basis 
is a numpy array of dimensions (number_of_basis_functions,length_ker_in_ms/dt). state is included in case we need dt or something else."""

	Nsteps = int(state.total_time/state.dt)

	Nbasis = copy.copy(np.shape(basis)[0])

	ST = np.zeros((len(spike_train),Nsteps),dtype='float')

	for i in range(len(spike_train)):

		indices = np.around(np.array(spike_train[i])*(1./state.dt))
		indices = indices.astype('int')
		indices = indices[indices<Nsteps]

		ST[i,indices] = 1.

	X = np.zeros((len(spike_train)*Nbasis,Nsteps),dtype='float')

	for i in range(np.shape(basis)[0]):

		X[len(spike_train)*i:len(spike_train)*(i+1),:] = signal.fftconvolve(ST,np.atleast_2d(basis[i,:]))[:,:Nsteps]
	
	return X
	

def likelihood(state):

	MP = MembPot(state)

	indices = np.around(np.array(state.output))
	indices = indices.astype('int')

	LL = np.sum(MP[indices]) - state.dt*np.sum(np.exp(MP))

	return LL

def gradient_NL(state):

	Nsteps = int(state.total_time/state.dt)
	Nb = np.shape(state.basisNL)[0]

	gradient_NL = np.zeros((state.Ng*Nb,Nsteps),dtype='float')

	MP = MembPot(state)
	MP12 = subMembPot(state)

	for g in range(state.Ng):

		u = MP12[g,:]

		for i in range(Nb-1):
			u = np.vstack((MP12[g,:],u))

		gradient_NL[g*Nb:(g+1)*Nb,:] = applyNL_2d(state.basisNL,u,state)

	sptimes = np.around(np.array(state.output[0])/state.dt)
	sptimes = sptimes.astype('int')

	gradient_NL = np.sum(gradient_NL[:,sptimes],axis=1) -state.dt*np.sum(gradient_NL*np.exp(MP),axis=1)

	return gradient_NL

def hessian_NL(state):

	Nsteps = int(state.total_time/state.dt)
	Nb = np.shape(state.basisNL)[0]

	hessian_NL = np.zeros((Nb*state.Ng,Nb*state.Ng,Nsteps),dtype='float')

	MP = MembPot(state)
	MP12 = subMembPot(state)
	
	for g in range(state.Ng):
		for h in range(state.Ng):

			if g>=h:
				ug = np.repeat(MP12[g,:],Nb,axis=0)
				uh = np.repeat(MP12[h,:],Nb,axis=0)

				ug = applyNL_2d(state.basisNL,ug,state)
				uh = applyNL_2d(state.basisNL,uh,state)

				hessian_NL[g*Nb:(g+1)*Nb,h*Nb:(h+1)*Nb,:] = np.dot(ug,uh.transpose())*np.exp(MP)

	hessian_NL = -state.dt*np.sum(hessian_NL,axis=2)

	hessian_NL = 0.5*(hessian_NL+hessian_NL.transpose())

	return hessian_NL

def applyNL(NL,u,state):

	dv = (state.bnds[1] - state.bnds[0])*0.001

	u = u/dv
	u = np.around(u)
	u = u.astype('int')
	u = NL[u]

	return u

def applyNL_2d(NL,u,state):

	dv = (state.bnds[1] - state.bnds[0])*0.001

	u = u/dv
	u = np.around(u)
	u = u.astype('int')

	if len(u.shape)==1:

		res = np.zeros((np.shape(NL)[0],np.size(u)),dtype='float')

		for i in range(np.shape(NL)[0]):
			res[i,:] = NL[i,u]

	else:
		
		res = np.zeros((np.shape(NL)[0],np.shape(u)[0]),dtype='float')

		for i in range(np.shape(u)[0]):
			u[i,:] = NL[i,u[i,:]]

	return u

def gradient_ker(state):

	Nb = np.shape(state.basisKer)[0]
	Nsteps = int(state.total_time/state.dt)
	Nneur = int(state.N/state.Ng)
	N_ASP = len(state.knots_ASP)
	Nbnl = np.shape(state.basisNL)[0]

	gradient_ker = np.zeros((state.Ng*Nb*Nneur+N_ASP+1,Nsteps),dtype='float')

	MP12 = subMembPot(state)
	MP = MembPot(state)
	
	for g in range(state.Ng):

		Basis = state.basisKer

		X = convolve(state.input[g*Nneur:(g+1)*Nneur],Basis,state)

		nlDer = np.dot(state.paramNL[g*Nbnl:(g+1)*Nbnl],state.basisNLder)

		gradient_ker[g*Nb*Nneur:(g+1)*Nb*Nneur,:] = X*applyNL(nlDer,MP12[g,:],state)

	gradient_ker[state.Ng*Nb*Nneur:-1,:] = -convolve(state.output,state.basisASP,state)

	sptimes = np.around(np.array(state.output[0])/state.dt)
	sptimes = sptimes.astype('int')

	gradient_ker = np.sum(gradient_ker[:,sptimes],axis=1) - state.dt*np.sum(gradient_ker*np.exp(MP),axis=1)

	gradient_ker[-1] = - len(state.output) + state.dt*np.sum(np.exp(MP))

	return gradient_ker

def hessian_ker(state):

	Nb = np.shape(state.basisKer)[0]
	Nsteps = int(state.total_time/state.dt)
	Nneur = int(state.N/state.Ng)
	N_ASP = len(state.knots_ASP)
	Nbnl = np.shape(state.basisNL)[0]

	gradient_ker = np.zeros((state.Ng*Nb*Nneur+N_ASP+1,Nsteps),dtype='float')

	MP12 = subMembPot(state)
	MP = MembPot(state)
	
	for g in range(state.Ng):

		Basis = state.basisKer

		X = convolve(state.input[g*Nneur:(g+1)*Nneur],Basis,state)
		
		nlDer = np.dot(state.paramNL[g*Nbnl:(g+1)*Nbnl],state.basisNLder)
		
		gradient_ker[g*Nb*Nneur:(g+1)*Nb*Nneur,:] = X*applyNL(nlDer,MP12[g,:],state)

	gradient_ker[state.Ng*Nb*Nneur:-1] = - convolve(state.output,state.basisASP,state)

	gradient_ker[-1] = - len(state.output) + state.dt*np.sum(np.exp(MP))

	Hess = -state.dt*np.dot(gradient_ker*np.exp(MP),gradient_ker.transpose())

	return Hess

def subMembPot(state):

	Nsteps = int(state.total_time/state.dt)

	MP12 = np.zeros((state.Ng,Nsteps),dtype='float')

	Nneur = int(state.N/state.Ng)
	Nb = state.N_cos_bumps

	for g in range(state.Ng):

		Basis = state.basisKer

		X = convolve(state.input[g*Nneur:(g+1)*Nneur],Basis,state)

		MP12[g,:] = np.dot(state.paramKer[g*Nneur*Nb:(g+1)*Nneur*Nb],X)

	return MP12

def MembPot(state):

	Nsteps = int(state.total_time/state.dt)

	MP = np.zeros(Nsteps)

	Nneurons = int(state.N/state.Ng)
	Nbnl = np.shape(state.basisNL)[0]

	MP12 = subMembPot(state)

	for g in range(state.Ng):

		Mp_g = MP12[g,:]

		F = state.basisNL

		NL = np.dot(F.transpose(),state.paramNL[g*Nbnl:(g+1)*Nbnl])

		dv = (state.bnds[1] - state.bnds[0])*0.001

		Mp_g = Mp_g/dv

		Mp_g = np.around(Mp_g)
		Mp_g = Mp_g.astype('int')

		Mp_g = NL[Mp_g]
	
		MP = MP + Mp_g

	X = convolve(state.output,state.basisASP,state)

	MP = MP - np.dot(state.paramKer[(-state.N_knots_ASP-1):-1],X) - state.paramKer[-1]

	return MP



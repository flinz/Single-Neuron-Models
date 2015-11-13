import numpy as np
import functions as fun
from scipy import signal
import diff_calc as diff

class State():

	def __init__(self,Model):

		gradient_ker = diff.gradient_ker(Model)
		gradient_nl = diff.gradient_NL(Model)

		hessian_ker = diff.hessian_ker(Model)
		hessian_nl = diff.hessian_NL(Model)

		self.paramKer = Model.paramKer
		self.paramNL = Model.paramNL

		self.likelihood = diff.likelihood(Model)

	def iter_ker(self,Model):

		self.paramKer = self.paramKer - np.dot(np.linalg.inv(self.hessian_ker),self.gradient_ker)

	def iter_NL(self):

		self.paramNL = self.paramNL - np.dot(np.linalg.inv(hessian_nl),self.gradient_NL)

	def update(self,Model):

		self.membrane_potential = membrane_potential(Model)

		self.likelihood = diff.likelihood(Model)
		
		self.gradient_ker = diff.gradient_ker(Model)
		self.hessian_ker = diff.hessian_ker(Model)

		self.gradient_NL = diff.gradient_NL(Model)
		self.hessian_NL = diff.hessian_NL(Model)
		
def BlockCoordinateAscent(Model):

	err = 1000.

	state = State(Model)
	
	while err>Model.tol:

		L0 = copy.copy(state.likelihood)

		state.iter_ker()
		state.update()

		err = state.likelihood - L0

		if err>Model.tol:

			L0 = copy.copy(state.likelihood)
		
			state.iter_NL()
			state.update()

			err = state.likelihood - L0
		
	return state.paramNL,state.paramKer,state.likelihood

	
	

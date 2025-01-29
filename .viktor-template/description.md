This application demonstrates how you can connect to a STAAD.Pro instance through a VIKTOR Worker. 
The app creates a steel structure in STAAD.Pro, generates a load case with self-weight and much more. 

This app uses the OpenSTAAD Application API, managed by comtypes, to launch, close, and create the model, as well as assign the relevant structural inputs. 
It also utilizes the Python library openstaad for retrieving the results.
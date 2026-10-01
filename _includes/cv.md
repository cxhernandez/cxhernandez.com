# Carlos Xavier Hernández

**Senior Research Scientist**
<br>
🐙 [github](https://github.com/cxhernandez) |
💼 [linkedin](https://linkedin.com/in/cxhernandez) |
🌐 [website](https://www.cxhernandez.com) |
✉️ [email](mailto:cxhrndz@gmail.com)



I am a Senior Research Scientist at [Meta Reality Labs](https://about.meta.com/realitylabs/), working on machine learning to enable [neuromotor interfaces](https://www.meta.com/emerging-tech/emg-wearable-technology/). Prior to that, I worked with [Vijay Pande](https://www.pandelab.org/) at Stanford on statistical modeling of biomolecular dynamics.




## Experience

### Meta Platforms, Inc.
**Senior Research Scientist** · New York, NY, USA · 2019 – Present

+ Shipped gesture recognition to consumers as the technical lead of a team of 8+ research scientists and engineers developing for the [Meta Neural Band](https://www.meta.com/ai-glasses/meta-ray-ban-display-glasses-and-neural-band/) (launched Sep 2025), by designing and training deep learning models that decode real-time sEMG and IMU signals into discrete input controls for [Meta Ray-Ban Display](https://www.meta.com/ai-glasses/meta-ray-ban-display-glasses-and-neural-band/) working under tight hardware constraints.
+ Achieved >90% gesture classification accuracy on held-out users without the need for individual calibration, by architecting a generic LSTM-based neural decoding model trained on large-scale sEMG datasets collected from ~5,000 participants. Co-authored [peer-reviewed publication in Nature](https://doi.org/10.1038/s41586-025-09255-w) demonstrating the first high-bandwidth non-invasive neuromotor interface with cross-user generalization (0.88 gestures/sec in closed-loop tests with first-time users), contributing core ML model development and evaluation methodology.
+ Demonstrated viability of [EMG-based controls for users with hand tremor](https://www.meta.com/blog/surface-emg-wristband-electromyography-human-computer-interaction-hci/) (featured at Meta Connect 2024), by leading cross-functional accessibility data collection and analysis to show that EMG-based models can accurately decode motor intent despite involuntary movement artifacts, achieving >80% gesture classification accuracy on the population with hand tremor.

### CTRL-labs (acquired by Meta, 2019)
**Research Scientist** · New York, NY, USA · 2018 – 2019

+ Built production-grade ML training and inference pipelines for personalization of real-time gesture recognition models, by developing end-to-end data processing, training, and fine-tuning infrastructure for wrist-based sEMG decoding.
+ Established foundational R&D for EMG-based neural interfaces prior to acquisition, by conducting early research on time-series signal processing and deep learning approaches for decoding motor signals into user intent.

### Stanford University
**NSF Graduate Research Fellow** · Stanford, CA, USA · 2013 – 2018

+ Authored [peer-reviewed publication in Phys. Rev. E](https://doi.org/10.1103/PhysRevE.97.062412) describing the Variational Dynamical Encoder (VDE), a time-lagged variational autoencoder that compresses high-dimensional time-series into a single interpretable, low-dimensional latent representation. The VDE retained over twice the mutual information with input features compared to linear methods, and on protein folding simulations resolved a slowest dynamical process 2× longer than the leading linear baseline (tICA).
+ Co-developed open-source scientific computing tools widely adopted across the computational biology community, by building Python libraries for molecular dynamics trajectory analysis, Markov state modeling of biomolecular kinetics, and automated hyperparameter optimization.
+ Achieved an R² of 0.987 and MSE of <0.1 in automated cell counting and segmentation, by training a convolutional neural network pipeline (FPN + VGG-11) with uncertainty estimation on ~10,000 microscopy images, replacing a time-intensive manual process with computer vision.



## Education

#### Stanford University
**Ph.D. in Biophysics** · Stanford, CA, USA · 2013 – 2018
<br>
*Advisor: [Vijay Pande](https://www.pandelab.org/)*

#### Columbia University in the City of New York
**B.S. in Applied Mathematics** · New York, NY, USA · 2009 – 2013



## Skills

**Languages & Frameworks:** Python, PyTorch, NumPy, SciPy, Pandas
<br>
**Domains:** Time-series modeling, signal processing (DSP), causal inference
<br>
**Methods:** Deep learning (RNNs, Transformers), large-scale distributed training, fine-tuning, Markov state models, information theory



## Selected Publications

#### A Generic Non-Invasive Neuromotor Interface for Human-Computer Interaction
P Kaifosh, TR Reardon, and **CTRL-labs** · *[Nature](https://doi.org/10.1038/s41586-025-09255-w)* · 2025<br>
📚 63

#### Variational Encoding of Complex Dynamics
**CX Hernández**\*, HK Wayment-Steele\*, MM Sultan\*, BE Husic, and VS Pande · *[Phys. Rev. E](https://doi.org/10.1103/PhysRevE.97.062412)* · 2018<br>
📚 149

#### Using Deep Learning for Segmentation and Counting within Microscopy Data
**CX Hernández**, MM Sultan, and VS Pande · *[arXiv](https://arxiv.org/abs/1802.10548)* · 2018<br>
📚 36



## Selected Software

#### MDTraj: A Modern, Open Library for the Analysis of Molecular Dynamics Trajectories
RT McGibbon, KA Beauchamp, MP Harrigan, C Klein, JM Swails, **CX Hernández**, CR Schwantes, LP Wang, TJ Lane, and VS Pande · [mdtraj/mdtraj](https://github.com/mdtraj/mdtraj) <br>
`Python` · ⭐ 689  · 🍴 290

#### VDE: Variational Dynamical Encoder for Complex Dynamics
**CX Hernández**, HK Wayment-Steele, MM Sultan, BE Husic, and VS Pande · [msmbuilder/vde](https://github.com/msmbuilder/vde)<br>
`Python` · ⭐ 189  · 🍴 42

#### MSMBuilder: Statistical Models for Biomolecular Dynamics
MP Harrigan, MM Sultan, **CX Hernández**, BE Husic, P Eastman, CR Schwantes, KA Beauchamp, RT McGibbon, and VS Pande · [msmbuilder/msmbuilder](https://github.com/msmbuilder/msmbuilder)<br>
`Python` · ⭐ 161  · 🍴 94

#### MolEncoder: Molecular Autoencoder in PyTorch
**CX Hernández** · [cxhernandez/molencoder](https://github.com/cxhernandez/molencoder)<br>
`Python` · ⭐ 92  · 🍴 18

#### Osprey: Hyperparameter Optimization for Machine Learning
RT McGibbon, **CX Hernández**, MP Harrigan, S Kearnes, MM Sultan, S Jastrzebski, BE Husic, and VS Pande · [msmbuilder/osprey](https://github.com/msmbuilder/osprey)<br>
`Python` · ⭐ 73  · 🍴 26


## Posters & Presentations

#### Neural Control of Movement Society Meeting
Poster · Panama City, PAN · 2025
*"Stable Control through sEMG Input: Hand Gesture Recognition on a Population with Hand Tremor"*

#### Convolutional Neural Networks for Visual Recognition (CS231N)
Invited Presentation · Stanford, CA, USA · 2017
*"Using Deep Learning for Segmentation and Counting within Microscopy Data"*

#### Biophysical Society Meeting
Poster · Los Angeles, CA, USA · 2016
*"Intrinsic Disorder in the P53 C-Terminal Regulatory Domain Yields Multiple Pathways for Folding-Upon-Binding"*

#### Workshop on Molecular and Chemical Kinetics
Poster · Berlin, DEU · 2015
*"Inferring Causality Along Transition State Pathways"*



## Honors & Awards

- Graduate Research Fellowship · National Science Foundation · 2013
- ADVANCE Summer Research Fellowship · Stanford University · 2013
- EXROP Undergraduate Research Fellowship · Howard Hughes Medical Institute · 2012
- Genentech Summer Undergraduate Research Fellowship · Columbia University · 2011



## Press

- [A Look at Our Surface EMG Research Focused on Equity and Accessibility](https://www.meta.com/blog/surface-emg-wristband-electromyography-human-computer-interaction-hci/) · *Meta* · 2024
- [Move Objects With Your Mind? We're Getting There, With The Help Of An Armband](https://www.npr.org/2019/07/16/717487081/video-move-objects-with-your-mind-were-getting-there-with-the-help-of-an-armband) · *NPR* · 2019
- [Pandemic Flu Risk Raised by Lax Hog-Farm Surveillance](https://www.wired.com/2012/06/missing-swine-flu/) · *Wired* · 2012

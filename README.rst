=======
Brubeck
=======

Brubeck is a Django app for creating and exploring a database of topological
information. It features:

- Automated proof generation. `Proof visualizations 
  <http://www.jdabbs.com/brubeck/michaels-closed-subspace/pseudocompact/proof/>`_ 
  are rendered using the `JavaScript InfoVis ToolKit <http://thejit.org/>`_.
- Searching for a space by its traits, or a full-text search.
- Full revision control of all entered text. Tools for reverting erroneous
  Traits and Implications.
- LaTeX rendering, courtesy of `MathJAX <http://www.mathjax.org/>`_.

The best way to get a feel for the site is by clicking around the 
`live instance <http://www.jdabbs.com/brubeck/>`_ running on Heroku.

About
=====
Brubeck is named after Dave Brubeck, a jazz pianist known for his use of
strange, mathematical time signatures.

The code for Brubeck is currently a one-man project, so documentation may be a
little sparse in areas that I'm confident future me will understand. If you're
interested in contributing to the project, though, feel free to contact me.

Planned features
================
The following are a list of things I plan to add, in no particular order. If
you'd like to start hacking away on any of them, please let me know:

- Support for aliases (\(T_2\), T_2 & Hausdorff)
- Improved text editing / revision management interfaces
- Integration with Mizar, Isabelle, ...
- Support for caching
- Support for asynchronous prover tasks (using celery)
- Improved search
- Styling beyond bootstrap defaults :)
- Mobile version of the site (Android / iPhone apps?)
- Support for cardinal-, group-, ring- ... valued properties
- Tools for finding and exploring conjectures, detecting impossible searches
  (like T_2 + ~T_1)
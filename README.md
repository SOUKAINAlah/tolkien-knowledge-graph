## SHACL validation
We validate the RDF exports with pySHACL.
Example:
python -m pyshacl .\data\rdf\elrond.ttl -s .\shapes\personShape.ttl -f human

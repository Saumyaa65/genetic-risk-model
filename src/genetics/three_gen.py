"""
Three-generation genetics model.

Implements genetic risk calculation across three generations:
grandparent -> parent -> child.

Uses joint genotype enumeration and Bayesian inference to compute
posterior probabilities given observed phenotypes.
"""

from typing import Dict, Any, List, Tuple, Optional
from .model import GeneticsModel
from collections import defaultdict
import math


# Genotype states for different inheritance patterns
AUTOSOMAL_RECESSIVE_GENOTYPES = ["AA", "Aa", "aa"]  # AA=normal, Aa=carrier, aa=affected
AUTOSOMAL_DOMINANT_GENOTYPES = ["AA", "Aa", "aa"]  # AA=normal, Aa=affected (dominant), aa=rare affected
X_LINKED_MALE_GENOTYPES = ["XY", "XrY"]  # XY=normal, XrY=affected
X_LINKED_FEMALE_GENOTYPES = ["XX", "XrX", "XrXr"]  # XX=normal, XrX=carrier, XrXr=affected


class ThreeGenModel(GeneticsModel):
    """
    Three-generation genetics model.
    
    Handles grandparent-parent-child relationships for genetic risk calculation.
    Uses joint genotype enumeration and Bayesian inference.
    """
    
    def __init__(self, epsilon: float = 1e-10):
        """
        Initialize the three-generation model.
        
        Args:
            epsilon: Small value for numerical stability (avoid division by zero)
        """
        self.epsilon = epsilon
    
    def _get_genotype_prior(
        self,
        person: Dict[str, Any],
        inheritance_type: str,
        genotype: str,
        role: Optional[str] = None
    ) -> float:
        """
        Get prior probability for a specific genotype given person's observed status.
        
        Args:
            person: Dictionary with 'status' field
            inheritance_type: "autosomal_recessive", "autosomal_dominant", or "x_linked"
            genotype: Genotype string (e.g., "AA", "Aa", "aa")
            role: For x_linked, "mother" or "father" (optional)
        
        Returns:
            Prior probability of this genotype
        """
        status = person.get("status", "unknown")
        
        # If explicit genotype probability is provided, use it
        if "genotype_probabilities" in person:
            return person["genotype_probabilities"].get(genotype, 0.0)
        
        # Autosomal recessive
        if inheritance_type == "autosomal_recessive":
            if status == "affected":
                return 1.0 if genotype == "aa" else 0.0
            elif status == "carrier":
                return 1.0 if genotype == "Aa" else 0.0
            elif status == "unaffected":
                return 1.0 if genotype == "AA" else 0.0
            else:  # unknown
                # Use population priors
                carrier_prob = person.get("carrier_probability", 0.01)
                affected_prob = person.get("affected_probability", 0.0001)
                if genotype == "AA":
                    return 1.0 - carrier_prob - affected_prob
                elif genotype == "Aa":
                    return carrier_prob
                elif genotype == "aa":
                    return affected_prob
        
        # Autosomal dominant
        elif inheritance_type == "autosomal_dominant":
            if status == "affected" or status == "carrier":
                # Affected is typically heterozygous (Aa), rarely homozygous (aa)
                if genotype == "Aa":
                    return 0.99  # Most affected are heterozygous
                elif genotype == "aa":
                    return 0.01  # Rare homozygous affected
                else:
                    return 0.0
            elif status == "unaffected":
                return 1.0 if genotype == "AA" else 0.0
            else:  # unknown
                affected_prob = person.get("affected_probability", 0.001)
                if genotype == "AA":
                    return 1.0 - affected_prob
                elif genotype == "Aa":
                    return affected_prob * 0.99
                elif genotype == "aa":
                    return affected_prob * 0.01
        
        # X-linked
        elif inheritance_type == "x_linked":
            if role == "mother" or role == "parent2":
                if status == "affected":
                    return 1.0 if genotype == "XrXr" else 0.0
                elif status == "carrier":
                    return 1.0 if genotype == "XrX" else 0.0
                elif status == "unaffected":
                    return 1.0 if genotype == "XX" else 0.0
                else:  # unknown
                    carrier_prob = person.get("carrier_probability", 0.01)
                    affected_prob = person.get("affected_probability", 0.0001)
                    if genotype == "XX":
                        return 1.0 - carrier_prob - affected_prob
                    elif genotype == "XrX":
                        return carrier_prob
                    elif genotype == "XrXr":
                        return affected_prob
            else:  # father
                if status == "affected":
                    return 1.0 if genotype == "XrY" else 0.0
                elif status == "unaffected":
                    return 1.0 if genotype == "XY" else 0.0
                else:  # unknown
                    affected_prob = person.get("affected_probability", 0.0005)
                    if genotype == "XY":
                        return 1.0 - affected_prob
                    elif genotype == "XrY":
                        return affected_prob
        
        return 0.0
    
    def _transmission_probability(
        self,
        parent_genotype: str,
        child_genotype: str,
        inheritance_type: str,
        parent_sex: str,
        child_sex: str,
        other_parent_prior: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute Mendelian transmission probability P(child_genotype | parent_genotype).
        
        For autosomal inheritance, this computes the marginal probability over possible
        genotypes of the other parent (using population priors if not provided).
        
        Args:
            parent_genotype: Genotype of parent
            child_genotype: Genotype of child
            inheritance_type: "autosomal_recessive", "autosomal_dominant", or "x_linked"
            parent_sex: "male" or "female"
            child_sex: "male" or "female"
            other_parent_prior: Optional dict of genotype probabilities for other parent
        
        Returns:
            Transmission probability (0.0 to 1.0)
        """
        # Autosomal inheritance (same for recessive and dominant)
        if inheritance_type in ["autosomal_recessive", "autosomal_dominant"]:
            # Child genotype depends on both parents
            # We marginalize over possible genotypes of the other parent
            # Use default population priors if not provided
            if other_parent_prior is None:
                # Default population priors
                other_parent_prior = {
                    "AA": 0.99,  # Most individuals are homozygous normal
                    "Aa": 0.01,  # Carrier frequency
                    "aa": 0.0001  # Affected frequency
                }
            
            # Compute probability child gets genotype given this parent's contribution
            prob = 0.0
            
            # What allele does this parent transmit?
            if parent_genotype == "AA":
                parent_transmits = {"A": 1.0}  # Always transmits A
            elif parent_genotype == "aa":
                parent_transmits = {"a": 1.0}  # Always transmits a
            elif parent_genotype == "Aa":
                parent_transmits = {"A": 0.5, "a": 0.5}  # 50% each
            else:
                return 0.0
            
            # Sum over what other parent can transmit
            for other_gt, other_prior_prob in other_parent_prior.items():
                if other_prior_prob < self.epsilon:
                    continue
                
                # What allele does other parent transmit?
                if other_gt == "AA":
                    other_transmits = {"A": 1.0}
                elif other_gt == "aa":
                    other_transmits = {"a": 1.0}
                elif other_gt == "Aa":
                    other_transmits = {"A": 0.5, "a": 0.5}
                else:
                    continue
                
                # Compute probability child gets required alleles for target genotype
                for parent_allele, p_transmit in parent_transmits.items():
                    for other_allele, o_transmit in other_transmits.items():
                        # Child genotype from two alleles
                        alleles = sorted([parent_allele, other_allele])
                        if alleles == ["A", "A"]:
                            child_gt = "AA"
                        elif alleles == ["A", "a"] or alleles == ["a", "A"]:
                            child_gt = "Aa"
                        elif alleles == ["a", "a"]:
                            child_gt = "aa"
                        else:
                            continue
                        
                        if child_gt == child_genotype:
                            prob += p_transmit * o_transmit * other_prior_prob
            
            return prob
        
        # X-linked inheritance
        elif inheritance_type == "x_linked":
            # Default priors for other parent if not provided
            if other_parent_prior is None:
                if parent_sex == "male":
                    # Father's other parent (for GP->P) or mother's spouse (for P->C)
                    # Other parent is female for father, male for mother
                    other_parent_prior = {
                        "XX": 0.99,
                        "XrX": 0.01,
                        "XrXr": 0.0001
                    }
                else:  # parent_sex == "female"
                    # Other parent is male (father)
                    other_parent_prior = {
                        "XY": 0.9995,
                        "XrY": 0.0005
                    }
            
            if parent_sex == "male":
                # Father: always passes X to daughters, Y to sons
                if child_sex == "male":
                    # Son gets Y from father; X comes from mother (other parent)
                    # P(son genotype | father genotype, other parent=mother)
                    if child_genotype == "XY":
                        # Son gets Y from father (always) and X from mother
                        # Marginalize over mother genotypes
                        prob = 0.0
                        if parent_genotype == "XY" or parent_genotype == "XrY":
                            # Father provides Y; mother provides X
                            prob = other_parent_prior.get("XX", 0.99) * 1.0  # Mother XX gives X
                            prob += other_parent_prior.get("XrX", 0.01) * 0.5  # Mother XrX gives X with prob 0.5
                            prob += other_parent_prior.get("XrXr", 0.0001) * 0.0  # Mother XrXr always gives Xr
                        return prob
                    elif child_genotype == "XrY":
                        # Son gets Y from father and Xr from mother
                        prob = 0.0
                        if parent_genotype == "XY" or parent_genotype == "XrY":
                            prob = other_parent_prior.get("XX", 0.99) * 0.0  # Mother XX can't give Xr
                            prob += other_parent_prior.get("XrX", 0.01) * 0.5  # Mother XrX gives Xr with prob 0.5
                            prob += other_parent_prior.get("XrXr", 0.0001) * 1.0  # Mother XrXr always gives Xr
                        return prob
                    return 0.0
                else:  # daughter
                    # Daughter gets X from father and X from mother
                    if parent_genotype == "XY":
                        # Father contributes X (always)
                        # Marginalize over mother genotypes for daughter genotype
                        if child_genotype == "XX":
                            # Daughter XX: father gives X, mother gives X
                            return other_parent_prior.get("XX", 0.99) * 1.0 + \
                                   other_parent_prior.get("XrX", 0.01) * 0.5
                        elif child_genotype == "XrX":
                            # Daughter XrX: father gives X, mother gives Xr (or vice versa)
                            return other_parent_prior.get("XrX", 0.01) * 0.5 + \
                                   other_parent_prior.get("XrXr", 0.0001) * 1.0
                        elif child_genotype == "XrXr":
                            return 0.0  # Father XY can't contribute Xr
                    elif parent_genotype == "XrY":
                        # Father contributes Xr (always)
                        if child_genotype == "XX":
                            return 0.0  # Father XrY can't contribute X
                        elif child_genotype == "XrX":
                            # Daughter XrX: father gives Xr, mother gives X
                            return other_parent_prior.get("XX", 0.99) * 1.0 + \
                                   other_parent_prior.get("XrX", 0.01) * 0.5
                        elif child_genotype == "XrXr":
                            # Daughter XrXr: father gives Xr, mother gives Xr
                            return other_parent_prior.get("XrX", 0.01) * 0.5 + \
                                   other_parent_prior.get("XrXr", 0.0001) * 1.0
                    return 0.0
            else:  # parent_sex == "female" (mother)
                # Mother: passes one X to child (random)
                if child_sex == "male":
                    # Son gets single X from mother; Y from father (other parent)
                    if child_genotype == "XY":
                        # Son XY: mother gives X, father gives Y
                        if parent_genotype == "XX":
                            return 1.0  # Mother always gives X
                        elif parent_genotype == "XrX":
                            return 0.5  # Mother gives X with prob 0.5
                        elif parent_genotype == "XrXr":
                            return 0.0  # Mother always gives Xr
                    elif child_genotype == "XrY":
                        # Son XrY: mother gives Xr, father gives Y
                        if parent_genotype == "XX":
                            return 0.0  # Mother can't give Xr
                        elif parent_genotype == "XrX":
                            return 0.5  # Mother gives Xr with prob 0.5
                        elif parent_genotype == "XrXr":
                            return 1.0  # Mother always gives Xr
                    return 0.0
                else:  # daughter
                    # Daughter gets one X from mother and one X from father (other parent)
                    # Marginalize over father genotypes
                    if parent_genotype == "XX":
                        # Mother contributes X
                        if child_genotype == "XX":
                            # Daughter XX: mother X, father X
                            return other_parent_prior.get("XY", 0.9995) * 1.0
                        elif child_genotype == "XrX":
                            # Daughter XrX: mother X, father Xr
                            return other_parent_prior.get("XrY", 0.0005) * 1.0
                        elif child_genotype == "XrXr":
                            return 0.0
                    elif parent_genotype == "XrX":
                        # Mother contributes X or Xr with prob 0.5 each
                        if child_genotype == "XX":
                            # Daughter XX: mother X, father X
                            return 0.5 * other_parent_prior.get("XY", 0.9995) * 1.0
                        elif child_genotype == "XrX":
                            # Daughter XrX: (mother X, father Xr) or (mother Xr, father X)
                            return 0.5 * other_parent_prior.get("XrY", 0.0005) * 1.0 + \
                                   0.5 * other_parent_prior.get("XY", 0.9995) * 1.0
                        elif child_genotype == "XrXr":
                            # Daughter XrXr: mother Xr, father Xr
                            return 0.5 * other_parent_prior.get("XrY", 0.0005) * 1.0
                    elif parent_genotype == "XrXr":
                        # Mother always contributes Xr
                        if child_genotype == "XX":
                            return 0.0
                        elif child_genotype == "XrX":
                            # Daughter XrX: mother Xr, father X
                            return other_parent_prior.get("XY", 0.9995) * 1.0
                        elif child_genotype == "XrXr":
                            # Daughter XrXr: mother Xr, father Xr
                            return other_parent_prior.get("XrY", 0.0005) * 1.0
                    return 0.0
        
        return 0.0
    
    def _phenotype_likelihood(
        self,
        genotype: str,
        observed_status: str,
        inheritance_type: str,
        sex: str
    ) -> float:
        """
        Compute P(observed_status | genotype) - likelihood of observed phenotype given genotype.
        
        Args:
            genotype: Genotype string
            observed_status: "affected", "carrier", "unaffected", or "unknown"
            inheritance_type: Inheritance pattern
            sex: "male" or "female"
        
        Returns:
            Likelihood probability (0.0 to 1.0)
        """
        if observed_status == "unknown":
            return 1.0  # No information, so likelihood is 1.0
        
        # Autosomal recessive
        if inheritance_type == "autosomal_recessive":
            if observed_status == "affected":
                return 1.0 if genotype == "aa" else 0.0
            elif observed_status == "carrier":
                return 1.0 if genotype == "Aa" else 0.0
            elif observed_status == "unaffected":
                return 1.0 if genotype == "AA" else 0.0
        
        # Autosomal dominant
        elif inheritance_type == "autosomal_dominant":
            if observed_status == "affected" or observed_status == "carrier":
                return 1.0 if genotype in ["Aa", "aa"] else 0.0
            elif observed_status == "unaffected":
                return 1.0 if genotype == "AA" else 0.0
        
        # X-linked
        elif inheritance_type == "x_linked":
            if sex == "male":
                if observed_status == "affected":
                    return 1.0 if genotype == "XrY" else 0.0
                elif observed_status == "unaffected":
                    return 1.0 if genotype == "XY" else 0.0
            else:  # female
                if observed_status == "affected":
                    return 1.0 if genotype == "XrXr" else 0.0
                elif observed_status == "carrier":
                    return 1.0 if genotype == "XrX" else 0.0
                elif observed_status == "unaffected":
                    return 1.0 if genotype == "XX" else 0.0
        
        return 0.0
    
    def _enumerate_genotypes(self, inheritance_type: str, sex: str) -> List[str]:
        """
        Get list of possible genotypes for a given inheritance pattern and sex.
        
        Args:
            inheritance_type: "autosomal_recessive", "autosomal_dominant", or "x_linked"
            sex: "male" or "female"
        
        Returns:
            List of genotype strings
        """
        if inheritance_type in ["autosomal_recessive", "autosomal_dominant"]:
            return AUTOSOMAL_RECESSIVE_GENOTYPES.copy()
        elif inheritance_type == "x_linked":
            if sex == "male":
                return X_LINKED_MALE_GENOTYPES.copy()
            else:
                return X_LINKED_FEMALE_GENOTYPES.copy()
        return []
    
    def compute_risk(self, pedigree: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute risk using three-generation model with joint genotype enumeration.
        
        Args:
            pedigree: Dictionary with keys:
                - grandparent: dict with 'status' field
                - parent: dict with 'status' field
                - child: dict with 'status' field (optional, for prediction)
            params: Dictionary with keys:
                - inheritance_type: str
                - grandparent_sex: str (optional, defaults based on inheritance)
                - parent_sex: str (optional, defaults based on inheritance)
                - child_sex: str (optional, defaults to "male")
        
        Returns:
            Risk calculation result with min, max, confidence, joint_posteriors, marginal_posteriors
        """
        grandparent = pedigree.get("grandparent", {})
        parent = pedigree.get("parent", {})
        child = pedigree.get("child", {})
        
        inheritance_type = params.get("inheritance_type")
        if not inheritance_type:
            raise ValueError("inheritance_type is required in params")
        
        # Determine sexes (with defaults)
        grandparent_sex = params.get("grandparent_sex", "female")  # Default: maternal grandparent
        parent_sex = params.get("parent_sex", "female")  # Default: mother
        child_sex = params.get("child_sex", "male")
        
        # Get possible genotypes for each generation
        gp_genotypes = self._enumerate_genotypes(inheritance_type, grandparent_sex)
        p_genotypes = self._enumerate_genotypes(inheritance_type, parent_sex)
        c_genotypes = self._enumerate_genotypes(inheritance_type, child_sex)
        
        # Enumerate all joint genotype combinations
        joint_priors = {}
        joint_posteriors = {}
        
        total_prior = 0.0
        total_posterior = 0.0
        
        for gp_gt in gp_genotypes:
            # Prior for grandparent genotype
            gp_prior = self._get_genotype_prior(
                grandparent, inheritance_type, gp_gt,
                role="grandparent" if inheritance_type == "x_linked" else None
            )
            
            if gp_prior < self.epsilon:
                continue
            
            for p_gt in p_genotypes:
                # Transmission probability: P(parent_genotype | grandparent_genotype)
                # For GP->P, we need to account for the other parent of P (external to model)
                # Use population priors for the other parent of P
                other_parent_of_p_prior = {}
                if inheritance_type in ["autosomal_recessive", "autosomal_dominant"]:
                    other_parent_of_p_prior = {
                        "AA": 0.99,
                        "Aa": 0.01,
                        "aa": 0.0001
                    }
                # For x_linked, other parent is determined by parent_sex
                # If parent is female, other parent is male (father)
                # If parent is male, other parent is female (mother)
                elif inheritance_type == "x_linked":
                    if parent_sex == "female":
                        other_parent_of_p_prior = {
                            "XY": 0.9995,
                            "XrY": 0.0005
                        }
                    else:
                        other_parent_of_p_prior = {
                            "XX": 0.99,
                            "XrX": 0.01,
                            "XrXr": 0.0001
                        }
                
                trans_gp_to_p = self._transmission_probability(
                    gp_gt, p_gt, inheritance_type, grandparent_sex, parent_sex,
                    other_parent_prior=other_parent_of_p_prior
                )
                
                if trans_gp_to_p < self.epsilon:
                    continue
                
                # Prior for parent genotype (conditional on grandparent)
                # This is P(P|GP) * P(P_observed|P)
                p_prior_conditional = self._get_genotype_prior(
                    parent, inheritance_type, p_gt,
                    role="parent" if inheritance_type == "x_linked" else None
                )
                
                # Joint prior: P(GP) * P(P|GP) * P(P_observed|P)
                # But we also account for parent's observed status
                p_likelihood = self._phenotype_likelihood(
                    p_gt, parent.get("status", "unknown"), inheritance_type, parent_sex
                )
                
                for c_gt in c_genotypes:
                    # Transmission probability: P(child_genotype | parent_genotype)
                    # For P->C, we need to account for the other parent (not in model)
                    # Use population priors for the other parent
                    other_parent_prior = {}
                    if inheritance_type in ["autosomal_recessive", "autosomal_dominant"]:
                        other_parent_prior = {
                            "AA": 0.99,
                            "Aa": 0.01,
                            "aa": 0.0001
                        }
                    # For x_linked, other parent is father for mother->child, or mother for father->child
                    # But in 3-gen model, we're following GP->P->C lineage, so other parent is external
                    # Use default population priors
                    
                    trans_p_to_c = self._transmission_probability(
                        p_gt, c_gt, inheritance_type, parent_sex, child_sex,
                        other_parent_prior=other_parent_prior if other_parent_prior else None
                    )
                    
                    if trans_p_to_c < self.epsilon:
                        continue
                    
                    # Likelihood for child phenotype (if observed)
                    c_likelihood = self._phenotype_likelihood(
                        c_gt, child.get("status", "unknown"), inheritance_type, child_sex
                    )
                    
                    # Joint prior: P(GP) * P(P|GP) * P(C|P)
                    joint_key = (gp_gt, p_gt, c_gt)
                    joint_prior = gp_prior * trans_gp_to_p * p_prior_conditional * trans_p_to_c
                    
                    # Apply phenotype likelihoods
                    joint_posterior = joint_prior * p_likelihood * c_likelihood
                    
                    # Likelihood for grandparent phenotype (if observed)
                    gp_likelihood = self._phenotype_likelihood(
                        gp_gt, grandparent.get("status", "unknown"), inheritance_type, grandparent_sex
                    )
                    joint_posterior *= gp_likelihood
                    
                    joint_priors[joint_key] = joint_prior
                    joint_posteriors[joint_key] = joint_posterior
                    
                    total_prior += joint_prior
                    total_posterior += joint_posterior
        
        # Normalize joint posteriors
        if total_posterior < self.epsilon:
            # Zero likelihood - no valid genotype combinations match observations
            return {
                "min": 0.0,
                "max": 0.0,
                "confidence": "low",
                "model": "three_generation",
                "factors": ["No valid genotype combinations match observed phenotypes"],
                "joint_posteriors": {},
                "marginal_posteriors": {}
            }
        
        normalized_joint_posteriors = {
            key: prob / total_posterior
            for key, prob in joint_posteriors.items()
        }
        
        # Compute marginal posteriors
        marginal_gp = defaultdict(float)
        marginal_p = defaultdict(float)
        marginal_c = defaultdict(float)
        
        for (gp_gt, p_gt, c_gt), prob in normalized_joint_posteriors.items():
            marginal_gp[gp_gt] += prob
            marginal_p[p_gt] += prob
            marginal_c[c_gt] += prob
        
        # Compute child risk (probability child is affected)
        child_risk = 0.0
        for c_gt, prob in marginal_c.items():
            if inheritance_type == "autosomal_recessive" and c_gt == "aa":
                child_risk += prob
            elif inheritance_type == "autosomal_dominant" and c_gt in ["Aa", "aa"]:
                child_risk += prob
            elif inheritance_type == "x_linked":
                if child_sex == "male" and c_gt == "XrY":
                    child_risk += prob
                elif child_sex == "female" and c_gt == "XrXr":
                    child_risk += prob
        
        # Confidence based on entropy of posterior distribution
        entropy = -sum(p * math.log(p + self.epsilon) for p in marginal_c.values() if p > 0)
        max_entropy = math.log(len(c_genotypes))
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy
            if normalized_entropy < 0.3:
                confidence = "high"
            elif normalized_entropy < 0.7:
                confidence = "medium"
            else:
                confidence = "low"
        else:
            confidence = "high"
        
        return {
            "min": child_risk,
            "max": child_risk,
            "confidence": confidence,
            "model": "three_generation",
            "factors": [
                f"Grandparent status: {grandparent.get('status', 'unknown')}",
                f"Parent status: {parent.get('status', 'unknown')}",
                f"Child status: {child.get('status', 'unknown')}",
                f"Inheritance: {inheritance_type}",
                "Joint genotype enumeration across 3 generations"
            ],
            "joint_posteriors": {
                f"{gp}_{p}_{c}": prob
                for (gp, p, c), prob in normalized_joint_posteriors.items()
            },
            "marginal_posteriors": {
                "grandparent": dict(marginal_gp),
                "parent": dict(marginal_p),
                "child": dict(marginal_c)
            }
        }
    
    def bayesian_update(
        self,
        observations: Dict[str, Any],
        priors: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform Bayesian update given observed phenotypes.
        
        Uses the compute_risk method which already incorporates phenotype likelihoods,
        then extracts updated marginal posteriors.
        
        Args:
            observations: Dictionary with observed statuses:
                - grandparent: str (optional)
                - parent: str (optional)
                - child: str (optional)
            priors: Dictionary with prior information:
                - grandparent: dict with status and optional probabilities
                - parent: dict with status and optional probabilities
                - child: dict with status and optional probabilities
            params: Dictionary with model parameters
        
        Returns:
            Dictionary with updated_priors, posterior_probabilities, joint_posteriors, marginal_posteriors
        """
        # Build pedigree from priors and observations
        pedigree = {
            "grandparent": priors.get("grandparent", {}).copy(),
            "parent": priors.get("parent", {}).copy(),
            "child": priors.get("child", {}).copy()
        }
        
        # Update with observations
        if "grandparent" in observations:
            pedigree["grandparent"]["status"] = observations["grandparent"]
        if "parent" in observations:
            pedigree["parent"]["status"] = observations["parent"]
        if "child" in observations:
            pedigree["child"]["status"] = observations["child"]
        
        # Compute risk (which includes Bayesian update via likelihoods)
        result = self.compute_risk(pedigree, params)
        
        # Extract posterior information
        marginal_posteriors = result.get("marginal_posteriors", {})
        joint_posteriors = result.get("joint_posteriors", {})
        
        # Convert marginal posteriors to updated prior format
        updated_priors = {}
        posterior_probs = {}
        
        if "grandparent" in marginal_posteriors:
            # Get most likely genotype or average probability
            gp_probs = marginal_posteriors["grandparent"]
            updated_priors["grandparent"] = {
                "genotype_probabilities": gp_probs
            }
            # Compute carrier/affected probability
            inheritance_type = params.get("inheritance_type")
            if inheritance_type == "autosomal_recessive":
                carrier_prob = gp_probs.get("Aa", 0.0)
                affected_prob = gp_probs.get("aa", 0.0)
                posterior_probs["grandparent"] = {
                    "carrier_probability": carrier_prob,
                    "affected_probability": affected_prob
                }
        
        if "parent" in marginal_posteriors:
            p_probs = marginal_posteriors["parent"]
            updated_priors["parent"] = {
                "genotype_probabilities": p_probs
            }
            inheritance_type = params.get("inheritance_type")
            if inheritance_type == "autosomal_recessive":
                carrier_prob = p_probs.get("Aa", 0.0)
                affected_prob = p_probs.get("aa", 0.0)
                posterior_probs["parent"] = {
                    "carrier_probability": carrier_prob,
                    "affected_probability": affected_prob
                }
        
        if "child" in marginal_posteriors:
            c_probs = marginal_posteriors["child"]
            updated_priors["child"] = {
                "genotype_probabilities": c_probs
            }
        
        return {
            "updated_priors": updated_priors,
            "posterior_probabilities": posterior_probs,
            "joint_posteriors": joint_posteriors,
            "marginal_posteriors": marginal_posteriors
        }
    
    @property
    def model_name(self) -> str:
        """Return the model name."""
        return "three_generation"
    
    @property
    def generation_count(self) -> int:
        """Return the number of generations (3)."""
        return 3
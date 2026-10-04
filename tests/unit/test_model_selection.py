from copy import deepcopy
import json
import pytest
from src.evaluation.selection import select_configuration
from src.evaluation.model_configurations import resolve_configuration


def summaries(a=(3.,10.,-2.),b=(4.,11.,-1.)):
    def one(ten,finish,bias):return {'pooled_prediction':{'finish':{'bias_s':bias}},'pooled_equal_race':{'10':{'mae_s':ten},'finish':{'mae_s':finish}}}
    return {'wear':one(5.,12.,-2.3433399051303514),'ablation_a':one(*a),'ablation_b':one(*b)}


def test_selection_requires_joint_minimum_and_exact_bias_gate():
    assert select_configuration(summaries())['selected_configuration']=='ablation_a'
    assert select_configuration(summaries(a=(3.,10.,-2.34334)))['selected_configuration']=='ablation_b'
    assert select_configuration(summaries(a=(3.,11.,-1.),b=(4.,10.,-1.)))['selected_configuration']=='wear'
    assert select_configuration(summaries(a=(7.,16.,-1.),b=(8.,18.,-1.)))['selected_configuration']=='wear'
    assert select_configuration(summaries(a=(3.,10.,-3.),b=(4.,11.,-4.)))['selected_configuration']=='wear'


def test_absolute_and_signed_bias_rules_are_explicit_and_ties_preserve_baseline():
    s=summaries(a=(3.,10.,4.),b=(4.,11.,-1.))
    assert select_configuration(s,bias_rule='absolute')['selected_configuration']=='ablation_b'
    assert select_configuration(s,bias_rule='signed')['selected_configuration']=='ablation_a'
    assert select_configuration(summaries(a=(5.,12.,-1.),b=(5.,12.,-1.)))['selected_configuration']=='wear'
    with pytest.raises(ValueError):select_configuration(s,bias_rule='unknown')


def test_freeze_changes_only_default_profile_and_preserves_explicit_candidates(monkeypatch,tmp_path):
    import src.evaluation.model_configurations as m
    path=tmp_path/'freeze.json';monkeypatch.setattr(m,'FREEZE_PATH',path)
    assert resolve_configuration()[0]=='offsets'
    path.write_text(json.dumps({'configuration':'wear'}))
    assert resolve_configuration()[0]=='wear'
    assert resolve_configuration('ablation_a')[1]==(True,True,True,True,False)
    assert resolve_configuration('ablation_b')[1]==(True,True,True,False,False)
    with pytest.raises(ValueError):resolve_configuration('unknown')
